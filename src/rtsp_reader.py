import logging
import time
import cv2
import threading
import numpy as np
import platform
import subprocess


class RTSPReader:
    """
    优化的 RTSP 流读取器
    
    特性：
    - 独立线程持续读取最新帧，避免阻塞
    - 线程安全缓冲区，只保留最新帧（防止画面撕裂）
    - 优化的 VideoCapture 参数（FFmpeg backend、小缓冲区、TCP传输）
    - 自动重连机制
    - 兼容 cv2.VideoCapture 接口
    """
    
    def __init__(self, url, reconnect_interval=1, enable_diagnostics=False, use_hw_accel=None, smoothness_mode='balanced'):
        """
        初始化 RTSP 读取器
        
        Args:
            url: RTSP 流地址
            reconnect_interval: 重连间隔（秒）
            enable_diagnostics: 是否启用诊断模式（监控帧率和延迟）
            use_hw_accel: 是否使用硬件加速（None=自动检测，True=强制启用，False=禁用）
            smoothness_mode: 流畅度模式
                - 'smooth': 流畅度优先（保留更多帧，可能延迟稍高，画面更流畅）
                - 'balanced': 平衡模式（默认，兼顾流畅度和延迟）
                - 'low_latency': 低延迟优先（只保留最新帧，延迟最低，可能偶尔顿顿）
        """
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.enable_diagnostics = enable_diagnostics
        self.smoothness_mode = smoothness_mode  # 'smooth', 'balanced', 'low_latency'
        self.cap = None
        self.latest_frame = None
        self.latest_ret = False
        self.frame_lock = threading.Lock()
        self.read_thread = None
        self.stop_reading = False
        self.is_connected = False
        
        # 根据流畅度模式设置参数
        if smoothness_mode == 'smooth':
            # 流畅度优先：保留少量帧缓冲，减少顿顿感
            self.frame_buffer_size = 2  # 保留2帧缓冲
            self.frame_skip_threshold = 5  # 更宽松的跳帧阈值
            self.min_sleep_threshold = 0.002  # 2ms，更少的休眠
        elif smoothness_mode == 'low_latency':
            # 低延迟优先：只保留最新帧，延迟最低
            self.frame_buffer_size = 1  # 只保留1帧（当前实现）
            self.frame_skip_threshold = 2  # 更激进的跳帧
            self.min_sleep_threshold = 0.001  # 1ms
        else:  # 'balanced'
            # 平衡模式：默认设置
            self.frame_buffer_size = 1  # 只保留最新帧
            self.frame_skip_threshold = 3  # 中等跳帧阈值
            self.min_sleep_threshold = 0.001  # 1ms
        
        # 检测是否为 Jetson 设备并确定是否使用硬件加速
        self.is_jetson = self._detect_jetson()
        if use_hw_accel is None:
            self.use_hw_accel = self.is_jetson  # 自动检测：Jetson 设备默认启用
        else:
            self.use_hw_accel = use_hw_accel and self.is_jetson  # 只有 Jetson 才支持
        
        # 诊断统计信息
        self.diagnostics = {
            'source_fps': 0.0,  # 源帧率（从RTSP读取的帧率）
            'source_frame_count': 0,  # 源帧计数
            'source_last_update': time.time(),  # 上次更新源统计的时间
            'read_delays': [],  # 读取延迟列表（最近100次）
            'frame_intervals': [],  # 帧间隔列表（最近100次）
            'max_read_delay': 0.0,  # 最大读取延迟
            'avg_read_delay': 0.0,  # 平均读取延迟
            'max_frame_interval': 0.0,  # 最大帧间隔
            'avg_frame_interval': 0.0,  # 平均帧间隔
            'read_failures': 0,  # 读取失败次数
            'diagnostics_lock': threading.Lock(),  # 诊断数据锁
        }
        
        # 初始化 VideoCapture
        self._init_capture()
        
        # 启动读取线程
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        
        # 等待第一帧（最多等待 3 秒）
        self._wait_for_first_frame()
    
    def _detect_jetson(self):
        """检测是否为 Jetson 设备"""
        try:
            # 方法1: 检查 /sys/firmware/devicetree/base/model
            try:
                with open('/sys/firmware/devicetree/base/model', 'r') as f:
                    model = f.read().strip()
                    if 'jetson' in model.lower() or 'nvidia' in model.lower():
                        return True
            except:
                pass
            
            # 方法2: 检查 nvdec 是否可用
            try:
                result = subprocess.run(['ffmpeg', '-hide_banner', '-decoders'], 
                                       capture_output=True, text=True, timeout=2)
                if 'h264_nvdec' in result.stdout or 'hevc_nvdec' in result.stdout:
                    return True
            except:
                pass
            
            # 方法3: 检查平台架构
            machine = platform.machine().lower()
            if 'aarch64' in machine or 'arm64' in machine:
                # 进一步检查是否有 NVIDIA GPU
                try:
                    result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=2)
                    if result.returncode == 0:
                        return True
                except:
                    pass
            
            return False
        except Exception as e:
            logging.debug(f"Jetson detection failed: {e}")
            return False
    
    def _build_ffmpeg_options(self, rtsp_url):
        """
        构建 FFmpeg 选项字符串（用于硬件加速）
        
        Returns:
            str: FFmpeg 选项字符串
        """
        options = []
        
        if self.use_hw_accel:
            # Jetson 硬件加速选项
            # 使用 NVDEC 硬件解码器
            options.append('-hwaccel nvdec')
            options.append('-hwaccel_output_format cuda')
            # 自动选择解码器（h264_nvdec 或 hevc_nvdec）
            options.append('-c:v h264_nvdec')  # 默认 H.264，如果失败会尝试其他格式
            logging.info("启用 Jetson NVDEC 硬件加速")
        else:
            # 软件解码
            options.append('-c:v h264')
        
        # 将选项转换为 FFmpeg 参数格式
        # 注意：OpenCV 的 VideoCapture 不支持直接传递 FFmpeg 选项
        # 我们需要通过环境变量或 GStreamer pipeline 来实现
        # 这里我们使用 GStreamer pipeline（如果可用）
        return options
    
    def _check_gstreamer_plugin(self, plugin_name):
        """检查 GStreamer 插件是否可用"""
        try:
            result = subprocess.run(
                ['gst-inspect-1.0', plugin_name],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def _build_gstreamer_pipeline(self, rtsp_url):
        """
        构建 GStreamer pipeline（支持 Jetson 硬件加速）
        
        Returns:
            str: GStreamer pipeline 字符串，如果硬件加速不可用则返回 None
        """
        if self.use_hw_accel and self.is_jetson:
            # 检查 nvdec 插件是否可用
            if not self._check_gstreamer_plugin('nvdec'):
                logging.warning("GStreamer nvdec 插件不可用，跳过硬件加速 pipeline")
                return None
            
            # 尝试多种 pipeline 配置
            pipelines = [
                # 配置1: 标准 NVDEC pipeline（低延迟优化）
                (
                    f"rtspsrc location={rtsp_url} latency=0 drop-on-latency=true do-retransmission=false ! "
                    "rtph264depay ! "
                    "h264parse ! "
                    "nvdec ! "  # Jetson 硬件解码器
                    "nvvidconv ! "  # 格式转换
                    "video/x-raw,format=BGRx ! "
                    "videoconvert ! "
                    "video/x-raw,format=BGR ! "
                    "appsink drop=true sync=false max-buffers=1 emit-signals=false"
                ),
                # 配置2: 简化版本（如果配置1失败）
                (
                    f"rtspsrc location={rtsp_url} latency=0 ! "
                    "rtph264depay ! "
                    "h264parse ! "
                    "nvdec ! "
                    "nvvidconv ! "
                    "videoconvert ! "
                    "video/x-raw,format=BGR ! "
                    "appsink"
                ),
                # 配置3: 使用 nvdec 的特定参数
                (
                    f"rtspsrc location={rtsp_url} latency=0 ! "
                    "rtph264depay ! "
                    "h264parse ! "
                    "nvdec gpu-id=0 ! "
                    "nvvidconv ! "
                    "video/x-raw,format=BGRx ! "
                    "videoconvert ! "
                    "video/x-raw,format=BGR ! "
                    "appsink"
                ),
            ]
            
            # 返回第一个 pipeline（如果失败会在调用处尝试其他方法）
            logging.info("使用 GStreamer + NVDEC 硬件加速 pipeline（配置1）")
            return pipelines[0]
        else:
            # 软件解码 pipeline
            pipeline = (
                f"rtspsrc location={rtsp_url} latency=0 ! "
                "rtph264depay ! "
                "h264parse ! "
                "avdec_h264 ! "
                "videoconvert ! "
                "video/x-raw,format=BGR ! "
                "appsink"
            )
            return pipeline
    
    def _check_ffmpeg_hw_support(self):
        """检查 FFmpeg 是否支持硬件加速"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-hwaccels'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if 'nvdec' in result.stdout or 'cuda' in result.stdout:
                return True
        except:
            pass
        return False
    
    def _init_capture(self):
        """初始化 VideoCapture，使用优化的参数"""
        try:
            # 检查 FFmpeg 硬件加速支持
            ffmpeg_hw_support = False
            if self.use_hw_accel and self.is_jetson:
                ffmpeg_hw_support = self._check_ffmpeg_hw_support()
                if ffmpeg_hw_support:
                    logging.info("检测到 FFmpeg 支持硬件加速（NVDEC）")
            
            # 优先尝试使用 GStreamer backend（支持硬件加速）
            if self.use_hw_accel and self.is_jetson:
                pipeline = self._build_gstreamer_pipeline(self.url)
                if pipeline:
                    try:
                        # 尝试使用 GStreamer
                        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                        if self.cap.isOpened():
                            # 尝试读取一帧来验证 pipeline 是否真的工作
                            ret, frame = self.cap.read()
                            if ret and frame is not None:
                                logging.info("✅ 成功使用 GStreamer + NVDEC 硬件加速")
                                # 保存第一帧，因为后续的读取循环会需要它
                                with self.frame_lock:
                                    self.latest_frame = frame
                                    self.latest_ret = True
                            else:
                                logging.warning("GStreamer pipeline 打开但无法读取帧，回退到 FFmpeg")
                                if self.cap:
                                    self.cap.release()
                                self.cap = None
                        else:
                            logging.warning("GStreamer + NVDEC pipeline 无法打开，回退到 FFmpeg")
                            self.cap = None
                    except Exception as e:
                        logging.warning(f"GStreamer pipeline 异常: {e}，回退到 FFmpeg")
                        if self.cap:
                            try:
                                self.cap.release()
                            except:
                                pass
                        self.cap = None
                else:
                    logging.info("GStreamer 硬件加速不可用，使用 FFmpeg")
            
            # 如果 GStreamer 失败或未启用，使用 FFmpeg backend
            if self.cap is None or not self.cap.isOpened():
                # 构建优化的 RTSP URL，使用 TCP 传输并添加更多优化参数
                rtsp_url = self.url
                params = []
                
                # 使用 TCP 传输（更稳定）
                if 'rtsp_transport' not in rtsp_url:
                    params.append('rtsp_transport=tcp')
                
                # FFmpeg 优化参数（低延迟优化）
                # - stimeout: 设置 socket 超时（微秒），3秒超时（更快响应）
                params.append('stimeout=3000000')
                # - max_delay: 最大延迟（微秒），进一步减少缓冲
                params.append('max_delay=200000')  # 从500ms减少到200ms
                # - reorder_queue_size: 重排序队列大小，设为0禁用（减少延迟）
                params.append('reorder_queue_size=0')
                # - flags: 低延迟标志
                params.append('flags=low_delay')
                # - fflags: 快速seek和nogentle
                params.append('fflags=+genpts+discardcorrupt+nobuffer+fastseek')
                # - strict: 非严格模式，允许更多兼容性
                params.append('strict=experimental')
                
                # Jetson 硬件加速参数（通过 FFmpeg）
                if self.use_hw_accel and self.is_jetson:
                    # 参考 Frigate 的做法，使用 FFmpeg 硬件加速参数
                    # 通过环境变量设置 FFmpeg 选项（OpenCV 会读取）
                    import os
                    # 设置 FFmpeg 硬件加速选项
                    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = (
                        'hwaccel;nvdec|'
                        'hwaccel_output_format;cuda|'
                        'c:v;h264_nvdec'
                    )
                    logging.info("设置 FFmpeg 硬件加速选项（NVDEC）")
                
                if params:
                    separator = '&' if '?' in rtsp_url else '?'
                    rtsp_url = f"{rtsp_url}{separator}{'&'.join(params)}"
                
                # 使用 FFmpeg backend（更稳定）
                self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                if not self.cap.isOpened():
                    # 如果 FFmpeg 失败，尝试默认 backend
                    logging.warning("FFmpeg backend failed, trying default backend")
                    self.cap = cv2.VideoCapture(self.url)
            
            if self.cap.isOpened():
                # 设置最小缓冲区以减少延迟（只保留最新帧）
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # 设置读取超时（某些系统支持）
                try:
                    self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
                    self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000)  # 进一步减少超时时间到1秒
                except:
                    pass  # 某些系统不支持这些属性
                
                # 尝试设置其他性能相关属性
                try:
                    # 设置自动曝光（如果支持）
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 手动模式
                    # 设置自动白平衡（如果支持）
                    self.cap.set(cv2.CAP_PROP_AUTO_WB, 0)
                except:
                    pass  # 这些属性可能不支持，忽略错误
                
                self.is_connected = True
                hw_status = "硬件加速" if (self.use_hw_accel and self.is_jetson) else "软件解码"
                mode_desc = {
                    'smooth': '流畅度优先',
                    'balanced': '平衡模式',
                    'low_latency': '低延迟优先'
                }
                logging.info(f"RTSP connection established ({hw_status}, {mode_desc.get(self.smoothness_mode, '未知模式')}): {self.url}")
            else:
                logging.error(f"Failed to open RTSP stream: {self.url}")
                self.is_connected = False
                
        except Exception as e:
            logging.error(f"Error initializing RTSP capture: {e}")
            self.is_connected = False
    
    def _read_loop(self):
        """后台线程持续读取帧（全速读取，只保留最新帧）"""
        consecutive_failures = 0
        max_failures = 5  # 连续失败5次才认为断开
        last_frame_time = 0
        # 根据实际源帧率和流畅度模式动态调整
        if self.smoothness_mode == 'smooth':
            min_frame_interval = 1.0 / 60.0  # 60fps，更宽松
        elif self.smoothness_mode == 'low_latency':
            min_frame_interval = 1.0 / 120.0  # 120fps，更严格
        else:  # 'balanced'
            min_frame_interval = 1.0 / 120.0  # 120fps
        
        fast_frame_count = 0
        frame_skip_threshold = self.frame_skip_threshold
        min_sleep_threshold = self.min_sleep_threshold
        
        while not self.stop_reading:
            try:
                if self.cap is None or not self.cap.isOpened():
                    # 连接断开，尝试重连
                    if not self.is_connected:
                        time.sleep(self.reconnect_interval)
                        self._reconnect()
                        consecutive_failures = 0
                        continue
                
                # 记录读取开始时间（用于诊断）
                read_start_time = time.time() if self.enable_diagnostics else 0
                
                # 读取新帧
                ret, frame = self.cap.read()
                
                if ret and frame is not None:
                    # 读取成功，更新最新帧
                    current_time = time.time()
                    
                    # 诊断：记录读取延迟和帧间隔
                    if self.enable_diagnostics:
                        read_delay = current_time - read_start_time
                        frame_interval = current_time - last_frame_time if last_frame_time > 0 else 0
                        self._update_diagnostics(read_delay, frame_interval, success=True)
                    
                    with self.frame_lock:
                        # 直接替换，不复制（减少开销）
                        # 只在 read() 方法中需要时才复制
                        self.latest_frame = frame
                        self.latest_ret = True
                        self.is_connected = True
                    consecutive_failures = 0
                    
                    # 根据流畅度模式调整延迟控制策略
                    elapsed = current_time - last_frame_time
                    if last_frame_time > 0:
                        if self.smoothness_mode == 'smooth':
                            # 流畅度优先：减少休眠，保持帧率稳定
                            if elapsed < min_frame_interval:
                                fast_frame_count += 1
                                if fast_frame_count >= frame_skip_threshold:
                                    sleep_time = min_frame_interval - elapsed
                                    if sleep_time > min_sleep_threshold:
                                        time.sleep(sleep_time * 0.5)  # 只休眠一半时间，保持流畅
                            else:
                                fast_frame_count = 0
                        elif self.smoothness_mode == 'low_latency':
                            # 低延迟优先：更激进的跳帧和休眠
                            if elapsed < min_frame_interval:
                                fast_frame_count += 1
                                if fast_frame_count >= frame_skip_threshold:
                                    sleep_time = min_frame_interval - elapsed
                                    if sleep_time > min_sleep_threshold:
                                        time.sleep(sleep_time)
                            else:
                                fast_frame_count = 0
                        else:  # 'balanced'
                            # 平衡模式：标准策略
                            if elapsed < min_frame_interval:
                                fast_frame_count += 1
                                if fast_frame_count >= frame_skip_threshold:
                                    sleep_time = min_frame_interval - elapsed
                                    if sleep_time > min_sleep_threshold:
                                        time.sleep(sleep_time)
                            else:
                                fast_frame_count = 0
                    last_frame_time = current_time
                else:
                    # 读取失败
                    if self.enable_diagnostics:
                        self._update_diagnostics(0, 0, success=False)
                    
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        with self.frame_lock:
                            self.latest_ret = False
                            self.is_connected = False
                        logging.warning("RTSP frame read failed multiple times, connection may be lost")
                        consecutive_failures = 0
                        time.sleep(0.1)  # 短暂休眠后重试
                    else:
                        # 短暂休眠，避免快速重试导致 CPU 占用过高
                        time.sleep(0.01)
                
            except Exception as e:
                logging.error(f"Error in RTSP read loop: {e}")
                self.is_connected = False
                consecutive_failures = 0
                time.sleep(self.reconnect_interval)
                self._reconnect()
    
    def _reconnect(self):
        """重连 RTSP 流"""
        logging.info(f"Reconnecting to RTSP stream: {self.url}")
        try:
            if self.cap is not None:
                self.cap.release()
            self._init_capture()
        except Exception as e:
            logging.error(f"Reconnection failed: {e}")
            self.is_connected = False
    
    def _wait_for_first_frame(self, timeout=3):
        """等待第一帧到达（最多等待 timeout 秒）"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.frame_lock:
                if self.latest_ret and self.latest_frame is not None:
                    return True
            time.sleep(0.1)
        return False
    
    def read(self):
        """
        读取最新帧（兼容 cv2.VideoCapture.read()）
        
        Returns:
            (ret, frame): ret 表示是否成功，frame 是最新的帧
        """
        with self.frame_lock:
            if self.latest_frame is not None and self.latest_ret:
                # 返回最新帧的副本（确保线程安全）
                # 使用 numpy 的 copy 方法，比 frame.copy() 稍快
                frame = np.copy(self.latest_frame) if self.latest_frame is not None else None
                return True, frame
            else:
                return False, None
    
    def isOpened(self):
        """
        检查连接是否打开（兼容 cv2.VideoCapture.isOpened()）
        
        Returns:
            bool: 连接是否打开
        """
        return self.is_connected and (self.cap is not None and self.cap.isOpened())
    
    def get(self, prop_id):
        """
        获取属性（兼容 cv2.VideoCapture.get()）
        
        Args:
            prop_id: 属性 ID（如 cv2.CAP_PROP_FRAME_WIDTH）
        
        Returns:
            属性值，如果不可用则返回 0
        """
        if self.cap is not None and self.cap.isOpened():
            return self.cap.get(prop_id)
        return 0.0
    
    def _update_diagnostics(self, read_delay, frame_interval, success=True):
        """更新诊断统计信息"""
        with self.diagnostics['diagnostics_lock']:
            if success:
                # 更新源帧率统计
                self.diagnostics['source_frame_count'] += 1
                current_time = time.time()
                elapsed = current_time - self.diagnostics['source_last_update']
                
                if elapsed >= 1.0:  # 每秒更新一次帧率
                    self.diagnostics['source_fps'] = self.diagnostics['source_frame_count'] / elapsed
                    self.diagnostics['source_frame_count'] = 0
                    self.diagnostics['source_last_update'] = current_time
                
                # 记录读取延迟（保留最近100次）
                if read_delay > 0:
                    self.diagnostics['read_delays'].append(read_delay)
                    if len(self.diagnostics['read_delays']) > 100:
                        self.diagnostics['read_delays'].pop(0)
                    
                    # 计算平均和最大延迟
                    if self.diagnostics['read_delays']:
                        self.diagnostics['avg_read_delay'] = sum(self.diagnostics['read_delays']) / len(self.diagnostics['read_delays'])
                        self.diagnostics['max_read_delay'] = max(self.diagnostics['read_delays'])
                
                # 记录帧间隔（保留最近100次）
                if frame_interval > 0:
                    self.diagnostics['frame_intervals'].append(frame_interval)
                    if len(self.diagnostics['frame_intervals']) > 100:
                        self.diagnostics['frame_intervals'].pop(0)
                    
                    # 计算平均和最大帧间隔
                    if self.diagnostics['frame_intervals']:
                        self.diagnostics['avg_frame_interval'] = sum(self.diagnostics['frame_intervals']) / len(self.diagnostics['frame_intervals'])
                        self.diagnostics['max_frame_interval'] = max(self.diagnostics['frame_intervals'])
            else:
                self.diagnostics['read_failures'] += 1
    
    def get_diagnostics(self):
        """
        获取诊断信息
        
        Returns:
            dict: 包含诊断信息的字典
        """
        with self.diagnostics['diagnostics_lock']:
            return {
                'source_fps': round(self.diagnostics['source_fps'], 2),
                'avg_read_delay_ms': round(self.diagnostics['avg_read_delay'] * 1000, 2),
                'max_read_delay_ms': round(self.diagnostics['max_read_delay'] * 1000, 2),
                'avg_frame_interval_ms': round(self.diagnostics['avg_frame_interval'] * 1000, 2),
                'max_frame_interval_ms': round(self.diagnostics['max_frame_interval'] * 1000, 2),
                'read_failures': self.diagnostics['read_failures'],
                'is_connected': self.is_connected,
            }
    
    def print_diagnostics(self):
        """打印诊断信息（用于调试）"""
        diag = self.get_diagnostics()
        logging.info("=== RTSP 诊断信息 ===")
        logging.info(f"源帧率: {diag['source_fps']} fps")
        logging.info(f"平均读取延迟: {diag['avg_read_delay_ms']} ms")
        logging.info(f"最大读取延迟: {diag['max_read_delay_ms']} ms")
        logging.info(f"平均帧间隔: {diag['avg_frame_interval_ms']} ms")
        logging.info(f"最大帧间隔: {diag['max_frame_interval_ms']} ms")
        logging.info(f"读取失败次数: {diag['read_failures']}")
        logging.info(f"连接状态: {'已连接' if diag['is_connected'] else '未连接'}")
        
        # 诊断建议
        if diag['max_frame_interval_ms'] > 200:
            logging.warning("⚠️  检测到帧间隔较大，可能是源端卡顿或网络问题")
        if diag['avg_read_delay_ms'] > 100:
            logging.warning("⚠️  读取延迟较高，可能是网络或源端问题")
        if diag['source_fps'] < 10:
            logging.warning("⚠️  源帧率较低，可能是源端问题")
    
    def release(self):
        """
        释放资源（兼容 cv2.VideoCapture.release()）
        """
        self.stop_reading = True
        if self.read_thread is not None and self.read_thread.is_alive():
            self.read_thread.join(timeout=2)
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_connected = False
        if self.enable_diagnostics:
            self.print_diagnostics()
        logging.info("RTSP reader released")

