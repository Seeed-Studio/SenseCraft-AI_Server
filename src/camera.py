import logging
import time
import cv2
from threading import Thread
from queue import Queue, Empty
from ultralytics import YOLO
from output import StreamingOutput
from rtsp_reader import RTSPReader


class Camera:
    def __init__(self, output: StreamingOutput, url, modelpath, task, classes=None, enable_diagnostics=False, async_inference=True):
        self.output = output
        self.url = url
        self.modelpath = modelpath
        self.track = False
        self.predictParams = {}
        self.infering = True
        self.real_fps = None
        self.enable_diagnostics = enable_diagnostics
        self.async_inference = async_inference  # 是否使用异步推理

        self.task = task or "detect"
        """
        task= 'detect', 'segment', 'classify', or 'pose'
        """

        # 设置classes参数，默认为[0]
        if classes is not None:
            self.predictParams["classes"] = classes
        else:
            self.predictParams["classes"] = [0]

        self.reconnect_interval = 1
        """
        reconnect interval, default is 1 seconds
        """
        
        # 处理帧率统计（用于诊断）
        self.process_frame_count = 0
        self.process_last_update = time.time()
        self.process_fps = 0.0
        self.infer_times = []  # 推理时间列表（最近100次）
        self.max_infer_time = 0.0
        self.avg_infer_time = 0.0
        
        # 异步推理相关
        if self.async_inference:
            self.inference_queue = Queue(maxsize=2)  # 最多保留2帧待推理
            self.inference_thread = None
            self.stop_inference = False
            logging.info("启用异步推理模式：推理不会阻塞视频流读取")

    def __enter__(self):
        self.load_mode()
        if self.mode == "image":
            self.init_image()
        else:
            self.init_stream()
        logging.info(
            "src[{}] fps[{}] width[{}] height[{}] model[{}] classes[{}]".format(
                self.url,
                self.fps,
                self.width,
                self.height,
                self.modelpath,
                self.predictParams.get("classes", [0]),
            )
        )
        self.model = YOLO(self.modelpath, task=self.task)
        try:
            if str(self.modelpath).endswith(".engine"):
                logging.info("使用 TensorRT Engine 模型进行推理: %s", self.modelpath)
            elif str(self.modelpath).endswith(".onnx"):
                logging.info("使用 ONNX 模型进行推理: %s", self.modelpath)
            else:
                logging.info("使用 PyTorch 模型进行推理: %s", self.modelpath)
        except Exception:
            pass
        self.stop_capture = False
        self.thread = Thread(target=self.capture)
        self.thread.start()
        
        # 如果启用异步推理，启动推理线程
        if self.async_inference:
            self.inference_thread = Thread(target=self._inference_worker, daemon=True)
            self.inference_thread.start()
            logging.info("异步推理线程已启动")
        
        return self

    def load_mode(self):
        """
        set the mode "how Camera Deal with the frame"
        - stream: keep getting frame
        - image: load once
        """
        self.mode = "stream"
        try:
            if str(self.url).split(".")[-1] in ["jpeg", "png", "jpg"]:
                self.mode = "image"
        except:
            pass

    def init_image(self):
        self.pic = cv2.imread(self.url)
        height, width, channels = self.pic.shape
        self.width = width
        self.height = height
        self.cap = None
        self.fps = None

    def init_stream(self):
        self.pic = None
        # 检测是否为 RTSP 流，如果是则使用优化的 RTSP 读取器
        if str(self.url).startswith("rtsp://"):
            # RTSPReader 会自动检测 Jetson 并启用硬件加速
            # smoothness_mode: 'smooth'(流畅度优先), 'balanced'(平衡), 'low_latency'(低延迟优先)
            self.cap = RTSPReader(
                self.url, 
                reconnect_interval=self.reconnect_interval, 
                enable_diagnostics=self.enable_diagnostics,
                use_hw_accel=None,  # None = 自动检测，Jetson 设备会自动启用
                smoothness_mode='low_latency'  # 默认平衡模式，可根据需要调整
            )
        else:
            self.cap = cv2.VideoCapture(self.url)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def check_connection_cap(self):
        # RTSPReader 已经内置自动重连机制，只需要检查状态
        if isinstance(self.cap, RTSPReader):
            # RTSPReader 会自动重连，这里只需要返回 cap
            return self.cap
        # 对于普通的 VideoCapture，保持原有逻辑
        if not self.cap.isOpened():
            logging.warning("cap lost, reconnecting...")
            self.cap.release()
            time.sleep(self.reconnect_interval)
            self.cap = cv2.VideoCapture(self.url)
        return self.cap

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_capture = True
        
        # 停止异步推理线程
        if self.async_inference:
            self.stop_inference = True
            if self.inference_thread and self.inference_thread.is_alive():
                self.inference_thread.join(timeout=2)
        
        self.thread.join()
        if self.cap:
            self.cap.release()

    def capture(self):
        """
        main loop:
        - 1 if not stop, get next frame
        - 2 handle replay
        - 3 infer the frame
        - 4 calculate fps
        - goto 1
        """
        last_diag_print = time.time()
        diag_print_interval = 10.0  # 每10秒打印一次诊断信息
        
        while not self.stop_capture:
            start = time.time()
            if self.mode == "stream":
                cap = self.check_connection_cap()
                ret, frame = cap.read()
            else:
                ret, frame = (True, self.pic)
            if not ret:
                self.handle_end()
            else:
                if self.async_inference:
                    # 异步推理模式：将帧放入队列，不阻塞
                    try:
                        # 如果队列满了，丢弃最旧的帧，放入新帧
                        if self.inference_queue.full():
                            try:
                                self.inference_queue.get_nowait()  # 丢弃最旧的帧
                            except Empty:
                                pass
                        self.inference_queue.put_nowait(frame)
                    except Exception as e:
                        logging.warning(f"异步推理队列错误: {e}")
                    # 异步模式下，读取帧的延迟不受推理影响
                else:
                    # 同步推理模式：阻塞直到推理完成
                    infer_start = time.time() if self.enable_diagnostics else 0
                    self.infer(frame)
                    if self.enable_diagnostics and infer_start > 0:
                        infer_time = time.time() - infer_start
                        self._update_process_diagnostics(infer_time)
            self.adjust_fps(start)
            
            # 定期打印诊断信息
            if self.enable_diagnostics and time.time() - last_diag_print >= diag_print_interval:
                self.print_diagnostics()
                last_diag_print = time.time()

    def adjust_fps(self, start):
        """
        adjust and calculate fps by the cost
        优化：减少不必要的 sleep，提高流畅度
        """
        cost = time.time() - start
        target_fps = int(self.fps or 60)
        frame_duration = 1.0 / target_fps
        
        # 只在处理时间明显小于帧间隔时才休眠
        # 如果处理时间接近或超过帧间隔，不休眠以保持流畅度
        if cost < frame_duration * 0.8:  # 只有处理时间小于80%帧间隔时才休眠
            sleep_time = frame_duration - cost
            # 只休眠超过2ms的情况，避免频繁微休眠
            if sleep_time > 0.002:
                time.sleep(sleep_time)
        
        real_cost = time.time() - start
        # avg fps with two frame, slow down fps change range, for human easy to see
        fps_new = int(1.0 / real_cost)
        self.real_fps = int(((self.real_fps or fps_new) + fps_new) / 2)

    def handle_end(self):
        """
        when source end or disconnect, replay or reconnect
        """
        if str(self.url).endswith(".mp4"):
            # 只有 VideoCapture 对象才支持 set 方法
            if not isinstance(self.cap, RTSPReader):
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if str(self.url).startswith("rtsp://"):
            # RTSPReader 已经内置自动重连机制，这里不需要手动处理
            # 但可以触发一次重连检查
            if isinstance(self.cap, RTSPReader):
                logging.warning("rtsp lost, RTSPReader will auto-reconnect...")
                # RTSPReader 会自动重连，无需手动处理
            else:
                # 兼容旧代码（如果仍使用 VideoCapture）
                logging.warning("rstp lost, reconnecting...")
                self.cap.release()
                time.sleep(self.reconnect_interval)
                self.cap = cv2.VideoCapture(self.url)
        if str(self.url).startswith("/dev/video"):
            logging.warning("usb-cam lost, reconnecting...")
            self.cap.release()
            time.sleep(self.reconnect_interval)
            self.cap = cv2.VideoCapture(self.url)
        # ignore the others, maybe not right

    def _update_process_diagnostics(self, infer_time):
        """更新处理诊断统计"""
        self.process_frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.process_last_update
        
        if elapsed >= 1.0:  # 每秒更新一次处理帧率
            self.process_fps = self.process_frame_count / elapsed
            self.process_frame_count = 0
            self.process_last_update = current_time
        
        # 记录推理时间（保留最近100次）
        if infer_time > 0:
            self.infer_times.append(infer_time)
            if len(self.infer_times) > 100:
                self.infer_times.pop(0)
            
            if self.infer_times:
                self.avg_infer_time = sum(self.infer_times) / len(self.infer_times)
                self.max_infer_time = max(self.infer_times)
    
    def get_diagnostics(self):
        """
        获取完整的诊断信息（包括源帧率和处理帧率对比）
        
        Returns:
            dict: 包含诊断信息的字典
        """
        diag = {
            'process_fps': round(self.process_fps, 2),
            'avg_infer_time_ms': round(self.avg_infer_time * 1000, 2),
            'max_infer_time_ms': round(self.max_infer_time * 1000, 2),
            'async_inference': self.async_inference,
        }
        
        # 如果是 RTSP 流，添加源诊断信息
        if isinstance(self.cap, RTSPReader):
            source_diag = self.cap.get_diagnostics()
            diag.update({
                'source_fps': source_diag['source_fps'],
                'avg_read_delay_ms': source_diag['avg_read_delay_ms'],
                'max_read_delay_ms': source_diag['max_read_delay_ms'],
                'avg_frame_interval_ms': source_diag['avg_frame_interval_ms'],
                'max_frame_interval_ms': source_diag['max_frame_interval_ms'],
                'read_failures': source_diag['read_failures'],
            })
            
            # 计算帧率差异
            if source_diag['source_fps'] > 0:
                fps_diff = source_diag['source_fps'] - self.process_fps
                fps_diff_percent = (fps_diff / source_diag['source_fps']) * 100
                diag['fps_difference'] = round(fps_diff, 2)
                diag['fps_difference_percent'] = round(fps_diff_percent, 2)
        
        return diag
    
    def print_diagnostics(self):
        """打印完整的诊断信息（用于调试）"""
        diag = self.get_diagnostics()
        logging.info("=" * 50)
        logging.info("📊 视频流诊断信息")
        logging.info("=" * 50)
        
        if isinstance(self.cap, RTSPReader):
            logging.info("【源端信息（RTSP）】")
            logging.info(f"  源帧率: {diag['source_fps']} fps")
            logging.info(f"  平均读取延迟: {diag['avg_read_delay_ms']} ms")
            logging.info(f"  最大读取延迟: {diag['max_read_delay_ms']} ms")
            logging.info(f"  平均帧间隔: {diag['avg_frame_interval_ms']} ms")
            logging.info(f"  最大帧间隔: {diag['max_frame_interval_ms']} ms")
            logging.info(f"  读取失败次数: {diag['read_failures']}")
            logging.info("")
            logging.info("【处理端信息】")
            logging.info(f"  处理帧率: {diag['process_fps']} fps")
            logging.info(f"  平均推理时间: {diag['avg_infer_time_ms']} ms")
            logging.info(f"  最大推理时间: {diag['max_infer_time_ms']} ms")
            logging.info(f"  推理模式: {'异步（不阻塞）' if diag['async_inference'] else '同步（阻塞）'}")
            logging.info("")
            logging.info("【对比分析】")
            if 'fps_difference' in diag:
                logging.info(f"  帧率差异: {diag['fps_difference']} fps ({diag['fps_difference_percent']}%)")
            
            # 诊断建议
            if diag['max_frame_interval_ms'] > 200:
                logging.warning("  ⚠️  源端帧间隔较大（>200ms），可能是源端卡顿或网络问题")
            if diag['avg_read_delay_ms'] > 100:
                logging.warning("  ⚠️  读取延迟较高（>100ms），可能是网络或源端问题")
            if diag['source_fps'] < 10:
                logging.warning("  ⚠️  源帧率较低（<10fps），可能是源端问题")
            if diag['process_fps'] < diag['source_fps'] * 0.8:
                if not diag['async_inference']:
                    logging.warning("  ⚠️  处理帧率明显低于源帧率，可能是处理瓶颈（推理速度慢）")
                    logging.info("  💡 建议：启用异步推理模式（async_inference=True）可减少推理对延迟的影响")
                else:
                    logging.warning("  ⚠️  处理帧率明显低于源帧率，推理队列可能积压")
            if diag['avg_infer_time_ms'] > 100:
                if not diag['async_inference']:
                    logging.warning("  ⚠️  推理时间较长（>100ms），建议启用异步推理模式以减少延迟影响")
                else:
                    logging.warning("  ⚠️  推理时间较长（>100ms），但异步模式已启用，不影响视频流读取延迟")
        else:
            logging.info("【处理端信息】")
            logging.info(f"  处理帧率: {diag['process_fps']} fps")
            logging.info(f"  平均推理时间: {diag['avg_infer_time_ms']} ms")
            logging.info(f"  最大推理时间: {diag['max_infer_time_ms']} ms")
        
        logging.info("=" * 50)
    
    def _inference_worker(self):
        """异步推理工作线程"""
        while not self.stop_inference:
            try:
                # 从队列获取帧进行推理
                frame = self.inference_queue.get(timeout=0.1)
                
                if not self.infering:
                    # 如果推理被禁用，直接输出原始帧
                    self.output.write([None], frame)
                    continue
                
                infer_start = time.time() if self.enable_diagnostics else 0
                
                # 执行推理
                if self.track:
                    results = self.model.track(
                        frame,
                        device="0",
                        classes=[0],
                        persist=True,
                        tracker="bytetrack.yaml",
                        verbose=False,
                        **self.predictParams
                    )
                else:
                    results = self.model.predict(
                        frame, device="0", verbose=False, classes=[0], **self.predictParams
                    )
                
                # 输出结果
                self.output.write(results)
                
                # 更新诊断统计
                if self.enable_diagnostics and infer_start > 0:
                    infer_time = time.time() - infer_start
                    self._update_process_diagnostics(infer_time)
                    
            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logging.error(f"异步推理错误: {e}")
                continue
    
    def infer(self, frame):
        """
        同步推理方法（用于非异步模式）
        """
        # if stop infering, output is the original frame
        if not self.infering:
            self.output.write([None], frame)
            return None
        # if using track
        if self.track:
            # lapx>=0.5.2
            results = self.model.track(
                frame,
                device="0",
                classes=[0],
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                **self.predictParams
            )
        else:
            results = self.model.predict(
                frame, device="0", verbose=False, classes=[0], **self.predictParams
            )
        self.output.write(results)
