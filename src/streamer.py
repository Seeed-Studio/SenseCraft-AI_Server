import datetime
import json
import logging
import os
import socketserver
import traceback
import numpy as np
import cv2
from uuid import uuid4
from constant import RESULT_TOPIC, SOURCE_UPLOAD_HTML
import env_helper
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
from camera import Camera
from file_manager import FileMgr
from image_helper import RIGHT_DOWN, RIGHT_TOP, add_text, img_copy
from mqtt_driver import MqttDriver
from output import StreamingOutput
from utils import about_info, jpg, list_freecam
import time

# 设置日志级别为DEBUG以查看详细的调试信息
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

fileMgr = FileMgr()

# 全局MQTT数据缓存
mqtt_data_cache: dict = {"latest_data": None, "last_update": None}

# 全局轨迹历史缓存
track_history = {}
track_history_max_length = 50  # 每个轨迹最大保存的点数
track_history_cleanup_frames = 30  # 多少帧后清理丢失的目标
# 新增：记录每个track_id丢失的帧数
target_miss_counter = {}

# 全局绊线检测缓存
line_crossing_cache: dict = {
    "line_config": None,  # 绊线配置 {"enabled", "x1", "y1", "x2", "y2", "direction", "tolerance", "color", "thickness", "show_line", "show_counts"}
    "crossing_counts": {"enter": 0, "exit": 0},  # 进出计数
    "track_states": {},  # 每个track_id的状态记录
    "last_update": None,
}


def update_mqtt_cache(data):
    """更新MQTT数据缓存"""
    global mqtt_data_cache
    mqtt_data_cache["latest_data"] = data
    mqtt_data_cache["last_update"] = datetime.datetime.now()


def get_mqtt_cache():
    """获取MQTT数据缓存"""
    global mqtt_data_cache
    return mqtt_data_cache


def update_track_history(track_ids, boxes, max_length=50):
    """
    更新轨迹历史
    Args:
        track_ids: 追踪ID列表
        boxes: 边界框列表 [x1, y1, x2, y2]
        max_length: 最大轨迹长度
    """
    global track_history, target_miss_counter

    # 获取当前帧所有活跃的ID
    current_ids = set()

    logging.debug(
        f"更新轨迹历史: track_ids数量={len(track_ids) if track_ids is not None else 0}, boxes数量={len(boxes) if boxes is not None else 0}"
    )

    if track_ids is not None and boxes is not None:
        for track_id, box in zip(track_ids, boxes):
            if track_id is not None:
                track_id = int(track_id)
                current_ids.add(track_id)

                # 计算边界框中心点
                x1, y1, x2, y2 = box
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                logging.debug(
                    f"更新轨迹点: track_id={track_id}, 中心点=({center_x}, {center_y})"
                )

                # 初始化轨迹历史
                if track_id not in track_history:
                    track_history[track_id] = []
                    logging.debug(f"新建轨迹: track_id={track_id}")

                # 添加新的轨迹点
                track_history[track_id].append((center_x, center_y))

                # 限制轨迹长度
                if len(track_history[track_id]) > max_length:
                    track_history[track_id] = track_history[track_id][-max_length:]
                # 活跃ID，miss计数归零
                target_miss_counter[track_id] = 0

    # 更新丢失目标的计数
    for tid in list(track_history.keys()):
        if tid not in current_ids:
            target_miss_counter[tid] = target_miss_counter.get(tid, 0) + 1
            logging.debug(
                f"目标丢失: track_id={tid}, 丢失帧数={target_miss_counter[tid]}"
            )
            # 超过阈值，清除轨迹和计数
            if target_miss_counter[tid] >= track_history_cleanup_frames:
                track_history.pop(tid, None)
                target_miss_counter.pop(tid, None)
                logging.debug(f"清理轨迹: track_id={tid}")
        else:
            # 已在当前帧出现，已在上面归零
            pass


def update_line_crossing_config(config):
    """更新绊线配置"""
    global line_crossing_cache
    line_crossing_cache["line_config"] = config
    line_crossing_cache["last_update"] = datetime.datetime.now()
    logging.debug(f"绊线配置已更新: {config}")
    logging.debug(
        f"绊线显示配置: show_line={config.get('show_line', True)}, show_counts={config.get('show_counts', True)}"
    )


def get_line_crossing_config():
    """获取绊线配置"""
    global line_crossing_cache
    return line_crossing_cache["line_config"]


# 初始化绊线配置（从配置文件加载）
try:
    app_config = fileMgr.get_appConfig()
    if app_config.get("line_crossing"):
        update_line_crossing_config(app_config["line_crossing"])
        logging.debug("服务器启动时从配置文件加载绊线配置")
except Exception as e:
    logging.warning(f"服务器启动时加载绊线配置失败: {e}")


def reset_line_crossing_counts():
    """重置绊线计数"""
    global line_crossing_cache
    line_crossing_cache["crossing_counts"] = {"enter": 0, "exit": 0}
    line_crossing_cache["track_states"] = {}
    logging.debug("绊线计数已重置")


def get_line_crossing_counts():
    """获取绊线计数"""
    global line_crossing_cache
    return line_crossing_cache["crossing_counts"]


def check_line_crossing(track_id, current_point, line_config):
    """
    检查是否穿越绊线
    Args:
        track_id: 追踪ID
        current_point: 当前点坐标 (x, y)
        line_config: 绊线配置 {
            "enabled": bool,  # 是否启用
            "x1": int, "y1": int, "x2": int, "y2": int,  # 绊线坐标
            "direction": str,  # "horizontal" 或 "vertical"
            "tolerance": int,  # 检测容差
            "show_line": bool,  # 是否显示绊线
            "show_counts": bool  # 是否显示计数
        }
    Returns:
        crossing_type: "enter", "exit", 或 None
    """
    global line_crossing_cache, track_history

    if not line_config:
        logging.debug("绊线配置为空")
        return None

    if not line_config.get("enabled", False):
        logging.debug(f"绊线检测未启用: {line_config}")
        return None

    x, y = current_point
    x1, y1 = line_config["x1"], line_config["y1"]
    x2, y2 = line_config["x2"], line_config["y2"]
    direction = line_config.get("direction", "horizontal")
    tolerance = line_config.get("tolerance", 5)

    logging.debug(
        f"绊线检测详情: track_id={track_id}, 当前点=({x}, {y}), 绊线=({x1},{y1})-({x2},{y2}), 方向={direction}, 容差={tolerance}"
    )

    # 获取该track_id的历史状态
    track_states = line_crossing_cache["track_states"]
    if track_id not in track_states:
        track_states[track_id] = {"last_side": None, "last_cross_time": 0}

    current_time = time.time()
    last_cross_time = track_states[track_id]["last_cross_time"]

    # 防止短时间内重复触发（防抖）
    time_diff = current_time - last_cross_time
    if time_diff < 1.0:  # 1秒内不重复触发
        logging.debug(
            f"防抖机制: track_id={track_id}, 距离上次穿越={time_diff:.2f}秒, 跳过"
        )
        return None

    # 判断当前点在绊线的哪一侧
    if direction == "horizontal":
        # 水平线：上方为enter，下方为exit
        if y < y1 - tolerance:
            current_side = "above"  # 上方
        elif y > y1 + tolerance:
            current_side = "below"  # 下方
        else:
            current_side = "on_line"  # 在线上
    else:
        # 垂直线：左侧为enter，右侧为exit
        if x < x1 - tolerance:
            current_side = "left"  # 左侧
        elif x > x1 + tolerance:
            current_side = "right"  # 右侧
        else:
            current_side = "on_line"  # 在线上

    last_side = track_states[track_id]["last_side"]

    logging.debug(
        f"穿越方向判断: track_id={track_id}, 当前侧={current_side}, 上次侧={last_side}"
    )

    # 判断穿越类型
    crossing_type = None
    if direction == "horizontal":
        if last_side == "above" and current_side == "below":
            crossing_type = "enter"  # 从上方穿越到下方（进入）
        elif last_side == "below" and current_side == "above":
            crossing_type = "exit"  # 从下方穿越到上方（离开）
    else:
        if last_side == "left" and current_side == "right":
            crossing_type = "enter"  # 从左侧穿越到右侧（进入）
        elif last_side == "right" and current_side == "left":
            crossing_type = "exit"  # 从右侧穿越到左侧（离开）

    logging.debug(f"穿越类型判断: track_id={track_id}, 穿越类型={crossing_type}")

    # 更新状态
    if current_side != "on_line":
        track_states[track_id]["last_side"] = current_side

    if crossing_type:
        track_states[track_id]["last_cross_time"] = current_time
        line_crossing_cache["crossing_counts"][crossing_type] += 1
        logging.debug(
            f"绊线穿越检测: track_id={track_id}, type={crossing_type}, counts={line_crossing_cache['crossing_counts']}"
        )

    return crossing_type


def draw_line_crossing(img, line_config):
    """
    在图像上绘制绊线
    Args:
        img: 输入图像
        line_config: 绊线配置
    """
    if not line_config:
        return

    if not line_config.get("enabled", False):
        return

    if not line_config.get("show_line", True):
        return

    x1, y1 = line_config["x1"], line_config["y1"]
    x2, y2 = line_config["x2"], line_config["y2"]
    color_raw = line_config.get("color", (0, 255, 0))  # 默认绿色

    # 解析颜色参数，支持颜色名称字符串或BGR元组
    if isinstance(color_raw, str):
        color = parse_color_name(color_raw)
    else:
        color = color_raw

    # 确保颜色是3个元素的BGR元组
    if color is None or len(color) != 3:
        color = (0, 255, 0)  # 默认绿色

    thickness = line_config.get("thickness", 3)

    # 绘制绊线
    cv2.line(img, (x1, y1), (x2, y2), color, thickness)

    # 绘制方向箭头
    direction = line_config.get("direction", "horizontal")
    if direction == "horizontal":
        # 水平线：绘制上下箭头
        arrow_length = 20
        # 上方箭头（enter方向）
        cv2.arrowedLine(
            img, (x1, y1 - arrow_length), (x1, y1), (0, 255, 0), 2, tipLength=0.3
        )
        cv2.putText(
            img,
            "Enter",
            (x1 + 5, y1 - arrow_length - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )
        # 下方箭头（exit方向）
        cv2.arrowedLine(
            img, (x2, y2), (x2, y2 + arrow_length), (0, 0, 255), 2, tipLength=0.3
        )
        cv2.putText(
            img,
            "Exit",
            (x2 + 5, y2 + arrow_length + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
        )
    else:
        # 垂直线：绘制左右箭头
        arrow_length = 20
        # 左侧箭头（enter方向）
        cv2.arrowedLine(
            img, (x1 - arrow_length, y1), (x1, y1), (0, 255, 0), 2, tipLength=0.3
        )
        cv2.putText(
            img,
            "Enter",
            (x1 - arrow_length - 30, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )
        # 右侧箭头（exit方向）
        cv2.arrowedLine(
            img, (x2, y2), (x2 + arrow_length, y2), (0, 0, 255), 2, tipLength=0.3
        )
        cv2.putText(
            img, "Exit", (x2 + 5, y2 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
        )


def draw_line_crossing_counts(img, counts, position=(10, 30), line_config=None):
    """
    在图像上绘制绊线计数
    Args:
        img: 输入图像
        counts: 计数数据 {"enter": x, "exit": y}
        position: 显示位置 (x, y)
        line_config: 绊线配置，用于检查是否显示计数
    """
    if not counts:
        return

    # 检查是否显示计数
    if line_config is not None and not line_config.get("show_counts", True):
        return

    x, y = position

    # 绘制背景面板
    panel_width = 200
    panel_height = 60
    cv2.rectangle(
        img, (x, y - 25), (x + panel_width, y + panel_height), (0, 0, 0, 128), -1
    )
    cv2.rectangle(
        img, (x, y - 25), (x + panel_width, y + panel_height), (255, 255, 255), 2
    )

    # 绘制标题
    cv2.putText(
        img,
        "Counter",
        (x + 5, y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    # 绘制进入计数
    enter_text = f"Enter: {counts.get('enter', 0)}"
    cv2.putText(
        img, enter_text, (x + 5, y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
    )

    # 绘制离开计数
    exit_text = f"Exit: {counts.get('exit', 0)}"
    cv2.putText(
        img, exit_text, (x + 5, y + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2
    )


def draw_track_trails(img, track_history, trail_color=None, trail_thickness=2):
    """
    在图像上绘制轨迹线，支持随时间推移变浅变细
    Args:
        img: 输入图像
        track_history: 轨迹历史字典
        trail_color: 轨迹线颜色 (可以是颜色名称字符串或BGR元组)
        trail_thickness: 最大轨迹线粗细
    """
    # 解析颜色参数
    parsed_color = (
        parse_color_name(trail_color) if isinstance(trail_color, str) else trail_color
    )
    min_thickness = 1
    for track_id, points in track_history.items():
        if len(points) > 1:
            base_color = (
                generate_color_from_id(track_id)
                if parsed_color is None
                else parsed_color
            )
            # 确保颜色不为None
            if base_color is None:
                base_color = (0, 255, 0)  # 默认绿色

            n = len(points)
            for i in range(1, n):
                alpha = i / (n - 1) if n > 1 else 1.0  # 0~1，越靠近尾部alpha越大
                # 使用固定颜色，不渐变
                color = base_color
                # 粗细渐变：头部细，尾部粗
                thickness = int(min_thickness * (1 - alpha) + trail_thickness * alpha)
                cv2.line(img, points[i - 1], points[i], color, thickness)


def generate_color_from_id(track_id):
    """
    根据追踪ID生成唯一的颜色
    """
    try:
        # 使用简单的哈希算法生成颜色
        hash_val = hash(track_id) % 360
        # 转换为HSV颜色空间，然后转换为BGR
        hsv_color = np.array([[[hash_val, 255, 255]]], dtype=np.uint8)
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)
        return tuple(map(int, bgr_color[0, 0]))
    except Exception as e:
        logging.warning(f"生成颜色失败，使用默认颜色: {e}")
        return (0, 255, 0)  # 默认绿色


def parse_color_name(color_name):
    """
    将颜色名称转换为BGR元组
    Args:
        color_name: 颜色名称字符串
    Returns:
        BGR颜色元组 (B, G, R)
    """
    color_map = {
        "red": (0, 0, 255),  # BGR格式
        "green": (0, 255, 0),
        "blue": (255, 0, 0),
        "yellow": (0, 255, 255),
        "cyan": (255, 255, 0),
        "magenta": (255, 0, 255),
        "orange": (0, 165, 255),
        "purple": (128, 0, 128),
        "pink": (147, 20, 255),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }

    if color_name is None or color_name == "":
        return None  # 返回None表示使用自动生成颜色

    return color_map.get(color_name.lower(), (0, 0, 255))  # 默认红色


def clear_track_history():
    """
    清理轨迹历史缓存
    """
    global track_history
    track_history.clear()
    logging.debug("轨迹历史缓存已清理")


def safe_plot(result, show_box=True, box_color=None):
    """
    安全地绘制检测结果，处理NaN值
    Args:
        result: YOLO推理结果
        show_box: 是否显示检测框
        box_color: 检测框颜色 (BGR元组或颜色名称字符串)
    """
    if not show_box:
        return result.plot(boxes=False)

    try:
        # 解析颜色参数
        parsed_color = (
            parse_color_name(box_color) if isinstance(box_color, str) else box_color
        )

        if parsed_color is None:
            # 使用默认的YOLO plot方法
            return result.plot(boxes=True, txt_color=(255, 255, 255))
        else:
            # 使用自定义颜色绘制
            return custom_plot_boxes(result, parsed_color)
    except ValueError as e:
        if "NaN" in str(e):
            logging.warning("检测到NaN值，禁用检测框显示: {}".format(str(e)))
            return result.plot(boxes=False)
        else:
            raise e


def custom_plot_boxes(result, box_color=(0, 255, 0)):
    """
    使用自定义颜色绘制检测框
    Args:
        result: YOLO推理结果
        box_color: 检测框颜色 (BGR元组)
    Returns:
        绘制了检测框的图像
    """
    # 获取原始图像
    img = result.orig_img.copy()

    if result.boxes is not None:
        try:
            boxes = result.boxes.xyxy.cpu().numpy()  # 边界框坐标
            confs = result.boxes.conf.cpu().numpy()  # 置信度
            cls_ids = result.boxes.cls.cpu().numpy()  # 类别ID

            # 获取类别名称
            names = result.names

            # 确保所有数组都不为None且长度一致
            if (
                boxes is not None
                and confs is not None
                and cls_ids is not None
                and len(boxes) == len(confs) == len(cls_ids)
            ):
                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    x1, y1, x2, y2 = map(int, box)
                    class_name = names[int(cls_id)]

                    # 绘制边界框
                    cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)

                    # 准备标签文本
                    label = f"{class_name} {conf:.2f}"

                    # 计算文本大小
                    (text_width, text_height), _ = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                    )

                    # 绘制标签背景
                    cv2.rectangle(
                        img,
                        (x1, y1 - text_height - 10),
                        (x1 + text_width, y1),
                        box_color,
                        -1,
                    )

                    # 绘制标签文本
                    cv2.putText(
                        img,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2,
                    )
        except Exception as e:
            logging.warning(f"绘制检测框时出错: {e}")
            # 如果出错，返回原始图像
            pass

    return img


def parse_files(data, boundary):
    files = {}
    sections = data.split(boundary)
    for section in sections:
        if section and section != b"--\r\n":
            parts = section.split(b"\r\n\r\n")
            if len(parts) < 2:
                continue  # ignore invalid section
            headers = parts[0]
            file_data = parts[1][:-2]
            for header in headers.split(b"\r\n"):
                if (
                    not header.startswith(b"Content-Disposition")
                    or not b"filename" in header
                ):
                    continue  # ignore non-file
                name = header.split(b";")[1].split(b"=")[1][1:-1].decode()
                filename = header.split(b";")[2].split(b"=")[1][1:-1].decode()
                files[name] = {"filename": filename, "data": file_data}
    return files


class StreamingHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """重写日志方法，使用我们的日志系统"""
        logging.debug("HTTP {} - {}".format(self.address_string(), format % args))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_POST(self):
        try:
            if self.path == "/appConfigs":
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)
                fileMgr.set_appconfig(body)
                configsNow = fileMgr.get_appConfig()
                response = {"message": "update config ok", "configs": configsNow}
                self.send_json(response)
            elif self.path == "/reloadModels":
                fileMgr.init_model_list()
                response = {
                    "message": "重新加载模型列表成功",
                    "models": fileMgr.modelJson,
                }
                self.send_json(response)
                return None
            elif self.path == "/line/config":
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)
                try:
                    config = json.loads(body.decode())

                    # 设置默认值
                    if "show_line" not in config:
                        config["show_line"] = True
                    if "show_counts" not in config:
                        config["show_counts"] = True

                    # 更新内存中的绊线配置
                    update_line_crossing_config(config)

                    # 同时保存到配置文件
                    try:
                        app_config = fileMgr.get_appConfig()
                        app_config["line_crossing"] = config
                        fileMgr.set_appconfig(json.dumps(app_config))
                        logging.debug("绊线配置已保存到配置文件")
                    except Exception as save_error:
                        logging.warning(f"保存绊线配置到文件失败: {save_error}")

                    response = {
                        "success": True,
                        "message": "绊线配置已保存",
                        "config": config,
                        "config_help": {
                            "show_line": "是否在图像上显示绊线（默认true）",
                            "show_counts": "是否在图像上显示计数（默认true）",
                            "enabled": "是否启用绊线检测（默认false）",
                            "x1,y1,x2,y2": "绊线坐标",
                            "direction": "绊线方向（horizontal/vertical）",
                            "tolerance": "检测容差（像素）",
                            "color": "绊线颜色（BGR元组或颜色名称）",
                            "thickness": "绊线粗细",
                        },
                    }
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path == "/upload":
                try:
                    content_length = int(self.headers["Content-Length"])
                    content_type = self.headers["Content-Type"]
                    boundary = content_type.split("=")[1].encode()
                    filedata = self.rfile.read(content_length)
                    files = parse_files(filedata, boundary)

                    uploaded_files = []
                    for name in files:
                        filedata = files[name]["data"]
                        filename = files[name]["filename"]

                        # 根据文件扩展名判断是视频源还是模型文件
                        file_ext = os.path.splitext(filename)[1].lower()
                        if file_ext in {".pt", ".pth", ".onnx", ".engine"}:
                            # 模型文件
                            fileMgr.save_model(filename, filedata)
                            uploaded_files.append(
                                {"type": "model", "filename": filename}
                            )
                        else:
                            # 视频源文件
                            fileMgr.save_source(filename, filedata)
                            uploaded_files.append(
                                {"type": "source", "filename": filename}
                            )

                    # 返回JSON响应而不是HTML
                    response = {
                        "success": True,
                        "message": f"成功上传 {len(uploaded_files)} 个文件",
                        "files": uploaded_files,
                    }
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error("POST Unknown Error[{}].".format(str(e)))
            self.send_html(str(e), 404)

    def try_get_urlparams(self):
        query = parse.urlparse(self.path).query
        parsed_query = parse.parse_qs(query)
        result = {}
        for key, value in parsed_query.items():
            try:
                if value[0]:
                    result[key] = value[0]
            except:
                continue
        return result

    def urlparams_load(self):
        # default params
        src = fileMgr.sampleVideoPath
        fps = 30
        quality = 50
        model_id = "80-object-detect"  # object detect
        show_time = False  # show timestamp or not
        show_fps = False  # show fps or not
        show_box = None  # show box or not
        track = False  # use track or not
        show_trail = False  # show track trail or not
        trail_length = 50  # max trail length
        trail_thickness = 2  # trail line thickness
        trail_color = None  # trail color (None for auto color)
        box_color = None  # box color (None for default YOLO colors)
        half = False  # use half or not
        conf = 0.25  # degree of confidence
        max_det = 300  # max detect amount
        uuid = str(uuid4())  # uuid for mqtt to identify output belongs which stream
        font_scale = 1  # text font scale
        thickness = 3  # text thickness
        txt_color = 3  # text color
        way = 1  # not working for now
        infering = True  # infering ON or OFF
        try:
            # load option params from url
            query = self.try_get_urlparams()
            logging.debug(query)
            # TODO: How to be more elegant to deal with this
            if query.get("src"):
                src = fileMgr.find_source_path(query.get("src"))
            if query.get("fps"):
                fps = int(query.get("fps", "30"))
            if query.get("quality"):
                quality = int(query.get("quality", "50"))
            if query.get("model_id"):
                model_id = query.get("model_id")
            if query.get("track"):
                track = int(query.get("track", "0")) > 0
            if query.get("show_trail"):
                show_trail = int(query.get("show_trail", "0")) > 0
            if query.get("trail_length"):
                trail_length = int(query.get("trail_length", "50"))
            if query.get("trail_thickness"):
                trail_thickness = int(query.get("trail_thickness", "2"))
            if query.get("trail_color"):
                trail_color = query.get("trail_color")  # 可以是颜色名称或None
            if query.get("box_color"):
                box_color = query.get("box_color")  # 可以是颜色名称或None
            if query.get("half"):
                half = int(query.get("half", "0")) > 0
            if query.get("conf"):
                conf = float(query.get("conf", 0.25))
            if query.get("max_det"):
                max_det = int(query.get("max_det", "300"))
            if query.get("show_box"):
                show_box = int(query.get("show_box", "1")) > 0
            if query.get("uuid"):
                uuid = query.get("uuid")
            if query.get("show_time"):
                show_time = int(query.get("show_time", "0")) > 0
            if query.get("show_fps"):
                show_fps = int(query.get("show_fps", "0")) > 0
            if query.get("infering"):
                infering = int(query.get("infering", "1")) > 0
            if query.get("font_scale"):
                font_scale = int(query.get("font_scale", "1"))
            if query.get("thickness"):
                thickness = int(query.get("thickness", "3"))
            if query.get("txt_color"):
                txt_color = int(query.get("txt_color", "3"))
            if query.get("way"):
                way = int(query.get("way", "1"))
            logging.debug(
                "load user config successed. src = {}, fps = {}, quality = {}, model_id = {}, track = {}, show_trail = {}, trail_length = {}, trail_thickness = {}, trail_color = {}, box_color = {}, half = {}, conf = {}, max_det = {}, show_box = {}, uuid = {}, show_fps = {}, infering = {}".format(
                    src,
                    fps,
                    quality,
                    model_id,
                    track,
                    show_trail,
                    trail_length,
                    trail_thickness,
                    trail_color,
                    box_color,
                    half,
                    conf,
                    max_det,
                    show_box,
                    uuid,
                    show_fps,
                    infering,
                )
            )
        except Exception as e:
            logging.warning("user config bad. some of them using default config.")
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
        return {
            "src": src,
            "fps": fps,
            "quality": quality,
            "model_id": model_id,
            "show_time": show_time,
            "show_fps": show_fps,
            "show_box": show_box,
            "track": track,
            "show_trail": show_trail,
            "trail_length": trail_length,
            "trail_thickness": trail_thickness,
            "trail_color": trail_color,
            "box_color": box_color,
            "half": half,
            "conf": conf,
            "max_det": max_det,
            "uuid": uuid,
            "font_scale": font_scale,
            "thickness": thickness,
            "txt_color": txt_color,
            "way": way,
            "infering": infering,
        }

    def do_GET(self):
        try:
            client_ip = self.client_address[0]
            logging.debug(
                "🔗 客户端连接: {} - 请求路径: {}".format(client_ip, self.path)
            )

            if self.path.startswith("/stream"):
                cfg = self.urlparams_load()
                src = cfg["src"]
                fps = cfg["fps"]
                quality = cfg["quality"]
                model_id = cfg["model_id"]
                track = cfg["track"]
                show_trail = cfg["show_trail"]
                trail_length = cfg["trail_length"]
                trail_thickness = cfg["trail_thickness"]
                trail_color = cfg["trail_color"]
                box_color = cfg["box_color"]
                half = cfg["half"]
                conf = cfg["conf"]
                max_det = cfg["max_det"]
                show_box = cfg["show_box"]
                uuid = cfg["uuid"]
                show_fps = cfg["show_fps"]
                show_time = cfg["show_time"]
                font_scale = cfg["font_scale"]
                thickness = cfg["thickness"]
                txt_color = cfg["txt_color"]
                way = cfg["way"]
                infering = cfg["infering"]
                modelpath = fileMgr.get_modelpath(model_id)
                if not modelpath:
                    logging.error("AI model not found.")
                    self.send_html("AI model not found.")
                    return None
                task = fileMgr.task_by_model_id(model_id)
                if show_box is None:
                    show_box = not task in ["segment", "pose"]
                output = StreamingOutput()
                with Camera(output, url=src, modelpath=modelpath, task=task) as camera:
                    camera.track = track
                    # https://docs.ultralytics.com/modes/predict/#inference-sources
                    camera.predictParams = {
                        "half": half,
                        "conf": conf,
                        "max_det": max_det,
                        "iou": 0.1,
                    }
                    if camera.mode == "image" and camera.pic is None:
                        logging.error("Image Source not found.")
                        self.send_html("Image Source not found.", 404)
                        return None
                    if (
                        camera.mode == "stream"
                        and camera.cap
                        and not camera.cap.isOpened()
                    ):
                        logging.error("Video Source not found.")
                        self.send_html("Video Source not found.", 404)
                        return None
                    else:
                        mqtt_driver = None
                        if env_helper.is_mqtt_on():
                            ip, port, user, pwd = env_helper.mqtt_configs()
                            mqtt_driver = MqttDriver(ip, port, user, pwd)
                        self.send_mjpeg_headers()
                        logging.info(
                            "🎬 开始流媒体传输 - 客户端: {} - 模型: {} - 源: {}".format(
                                client_ip, model_id, src
                            )
                        )
                        try:
                            while True:
                                with output.condition:
                                    output.condition.wait()
                                    frame = self.get_one_frame(
                                        camera,
                                        mqtt_driver,
                                        fps,
                                        quality,
                                        uuid,
                                        show_box,
                                        show_trail,
                                        trail_length,
                                        trail_thickness,
                                        trail_color,
                                        box_color,
                                        show_fps,
                                        show_time,
                                        font_scale,
                                        thickness,
                                        txt_color,
                                        way,
                                        infering,
                                    )
                                self.wfile.write(b"--FRAME\r\n")
                                self.send_header("Content-Type", "image/jpeg")
                                self.send_header("Content-Length", str(len(frame)))
                                self.end_headers()
                                self.wfile.write(frame)
                                self.wfile.write(b"\r\n")
                        except Exception as e:
                            traceback.print_exc()
                            logging.warning(
                                "❌ 客户端断开连接 {}: {}".format(
                                    self.client_address, str(e)
                                )
                            )
                    return None
            elif self.path.startswith("/appConfigs"):
                logging.debug("📋 获取应用配置 - 客户端: {}".format(client_ip))
                response = fileMgr.get_appConfig()
                logging.debug(response)
                self.send_json(response)
                return None
            elif self.path.startswith("/about"):
                try:
                    response = about_info()
                    logging.debug(response)
                    self.send_json(response)
                except Exception as e:
                    traceback.print_exc()
                    logging.error(str(traceback.format_exc()))
                    logging.error("about Error[{}].".format(str(e)))
                    self.send_html(str(e), 400)
                return None
            elif self.path == "/camList":
                logging.debug("📷 获取摄像头列表 - 客户端: {}".format(client_ip))
                response = list_freecam()
                self.send_json(response)
                return None
            elif self.path == "/sources/upload":
                self.send_html(SOURCE_UPLOAD_HTML)
                return None
            elif self.path == "/sources/list":
                logging.debug("📁 获取源文件列表 - 客户端: {}".format(client_ip))
                response = fileMgr.list_source()
                logging.debug(response)
                self.send_json(response)
                return None
            elif self.path == "/models/list":
                logging.debug("🤖 获取模型列表 - 客户端: {}".format(client_ip))
                response = fileMgr.list_models()
                logging.debug("发现 {} 个模型".format(len(response["list"])))
                self.send_json(response)
                return None
            elif self.path == "/mqtt/data":
                logging.debug("📡 获取MQTT数据 - 客户端: {}".format(client_ip))
                response = self.get_mqtt_data()
                self.send_json(response)
                return None
            elif self.path.startswith("/sources/del"):
                try:
                    query = self.try_get_urlparams()
                    targetName = query.get("name")
                    if targetName and fileMgr.del_source(targetName):
                        response = {
                            "success": True,
                            "message": f"成功删除视频源: {targetName}",
                        }
                    else:
                        response = {
                            "success": False,
                            "message": f"删除视频源失败: {targetName}",
                        }
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path.startswith("/models/del"):
                try:
                    query = self.try_get_urlparams()
                    targetName = query.get("name")
                    if targetName and fileMgr.del_model(targetName):
                        response = {
                            "success": True,
                            "message": f"成功删除模型: {targetName}",
                        }
                    else:
                        response = {
                            "success": False,
                            "message": f"删除模型失败: {targetName}",
                        }
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path == "/track/clear":
                logging.debug("🧹 清理轨迹历史 - 客户端: {}".format(client_ip))
                try:
                    clear_track_history()
                    response = {"success": True, "message": "轨迹历史清理成功"}
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path == "/track/stats":
                logging.debug("📊 获取轨迹统计 - 客户端: {}".format(client_ip))
                try:
                    stats = {
                        "active_tracks": len(track_history),
                        "total_points": sum(
                            len(points) for points in track_history.values()
                        ),
                        "max_track_length": (
                            max(len(points) for points in track_history.values())
                            if track_history
                            else 0
                        ),
                        "track_ids": list(track_history.keys()),
                    }
                    response = {
                        "success": True,
                        "data": stats,
                        "message": "轨迹统计获取成功",
                    }
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path == "/line/config":
                logging.debug("📏 获取绊线配置 - 客户端: {}".format(client_ip))
                # 优先从配置文件加载绊线配置
                try:
                    app_config = fileMgr.get_appConfig()
                    if app_config.get("line_crossing"):
                        # 如果配置文件中有绊线配置，更新内存中的配置
                        update_line_crossing_config(app_config["line_crossing"])
                        logging.debug("从配置文件加载绊线配置")
                except Exception as e:
                    logging.warning(f"从配置文件加载绊线配置失败: {e}")

                response = get_line_crossing_config()
                self.send_json(response)
                return None
            elif self.path == "/line/reset":
                logging.debug("🧹 重置绊线计数 - 客户端: {}".format(client_ip))
                try:
                    reset_line_crossing_counts()
                    response = {"success": True, "message": "绊线计数已重置"}
                    self.send_json(response)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    error_response = {"success": False, "message": str(e)}
                    self.send_json(error_response, 400)
                return None
            elif self.path == "/line/counts":
                logging.debug("📊 获取绊线计数 - 客户端: {}".format(client_ip))
                response = get_line_crossing_counts()
                self.send_json(response)
                return None
            else:
                self.handle_static()
                return None
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error("Unknown Error[{}].".format(str(e)))
            self.send_html(str(e), 400)
        return None

    def handle_static(self):
        """
        static server for web-console
        """
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        mime_type, content = fileMgr.get_static(self.path)
        if content and mime_type:
            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.end_headers()
            self.wfile.write(content)
            return None
        else:
            logging.error("Error Url Path[{}]".format(self.path))
            self.send_html("Error Url Path[{}]".format(self.path), 404)
        return None

    def send_html(self, html: str | None = None, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if html:
            self.wfile.write(html.encode())

    def send_json_headers(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()

    def send_json(self, response, code=200):
        self.send_json_headers(code)
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

    def send_mjpeg_headers(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Age", "0")
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
        self.end_headers()

    def get_one_frame(
        self,
        camera: Camera,
        mqtt_driver: MqttDriver | None,
        fps,
        quality,
        uuid,
        show_box,
        show_trail,
        trail_length,
        trail_thickness,
        trail_color,
        box_color,
        show_fps,
        show_time,
        font_scale,
        thickness,
        txt_color,
        way,
        infering,
    ):
        if fps:
            camera.fps = fps
        camera.infering = infering
        try:
            if camera.output.results is None or len(camera.output.results) == 0:
                raise Exception("No results available from camera")
            result = camera.output.results[0]
            rawFrame = camera.output.orig_img
            if not camera.infering and rawFrame is not None:
                img = img_copy(rawFrame)
            else:
                if env_helper.is_mqtt_on() and mqtt_driver is not None:
                    viewInfo = self.handle_view_info(result, uuid)
                    mqtt_driver.publish(RESULT_TOPIC, json.dumps(viewInfo))

                img = safe_plot(result, show_box, box_color)

                # 如果启用了追踪和轨迹线显示
                if camera.track and show_trail and result.boxes is not None:
                    # 获取追踪ID和边界框
                    track_ids = result.boxes.id
                    boxes = result.boxes.xyxy

                    logging.debug(f"追踪数据: track_ids={track_ids}, boxes={boxes}")

                    # 确保track_ids和boxes都不为None且可迭代
                    if track_ids is not None and boxes is not None:
                        logging.debug(
                            f"有效追踪数据: track_ids数量={len(track_ids)}, boxes数量={len(boxes)}"
                        )

                        # 更新轨迹历史
                        update_track_history(track_ids, boxes, trail_length)

                        # 绘制轨迹线
                        draw_track_trails(
                            img, track_history, trail_color, trail_thickness
                        )

                        # 绊线检测逻辑
                        line_config = get_line_crossing_config()
                        logging.debug(f"绊线配置: {line_config}")

                        if line_config and line_config.get("enabled"):
                            logging.debug(f"绊线检测已启用，开始检测...")
                            # 对每个检测到的目标进行绊线检测
                            for track_id, box in zip(track_ids, boxes):
                                if track_id is not None:
                                    track_id = int(track_id)
                                    # 计算边界框中心点
                                    x1, y1, x2, y2 = box
                                    center_x = int((x1 + x2) / 2)
                                    center_y = int((y1 + y2) / 2)

                                    logging.debug(
                                        f"检测目标: track_id={track_id}, 中心点=({center_x}, {center_y})"
                                    )

                                    # 检查是否穿越绊线
                                    crossing_type = check_line_crossing(
                                        track_id, (center_x, center_y), line_config
                                    )
                                    if crossing_type:
                                        logging.debug(
                                            f"检测到绊线穿越: track_id={track_id}, type={crossing_type}"
                                        )
                        else:
                            logging.debug(
                                f"绊线检测未启用或配置无效: enabled={line_config.get('enabled') if line_config else None}"
                            )
                    else:
                        logging.debug(
                            f"追踪数据无效: track_ids={track_ids}, boxes={boxes}"
                        )
                else:
                    logging.debug(
                        f"追踪条件不满足: track={camera.track}, show_trail={show_trail}, result.boxes={result.boxes is not None}"
                    )

                # 绊线绘制和计数显示（独立于追踪条件）
                line_config = get_line_crossing_config()
                if line_config and line_config.get("show_line", True):  # 默认显示绊线
                    draw_line_crossing(img, line_config)
                if line_config and line_config.get("show_counts", True):  # 默认显示计数
                    draw_line_crossing_counts(
                        img, get_line_crossing_counts(), (10, 100), line_config
                    )

            self.handle_fps_time(
                show_fps,
                show_time,
                img,
                camera.real_fps,
                camera.fps,
                font_scale,
                thickness,
                txt_color,
                way,
            )
            frame = jpg(img, quality)
            return frame
        except Exception as e:
            raise e

    def handle_fps_time(
        self,
        show_fps,
        show_time,
        img,
        real_fps,
        fps,
        font_scale,
        thickness,
        txt_color,
        way,
    ):
        if show_fps:
            add_text(
                img,
                "fps: {:>3d}/{}".format(
                    real_fps,
                    fps,
                ),
                font_scale,
                thickness,
                txt_color,
                RIGHT_TOP or way,
            )
        if show_time:
            add_text(
                img,
                str(datetime.datetime.now())[:-7],
                font_scale,
                thickness,
                txt_color,
                RIGHT_DOWN or way,
            )

    def handle_view_info(self, result, uuid: str):
        """
        Visualization of results for humans
        """
        view = {
            "uuid": uuid,
            "info": {},
        }
        try:
            # just counter for now
            resObj = json.loads(result.to_json())
            for obj in resObj:
                if view["info"].get(obj["name"]):
                    view["info"][obj["name"]] += 1
                else:
                    view["info"][obj["name"]] = 1

            # 添加绊线计数数据
            line_counts = get_line_crossing_counts()
            view["line_crossing"] = line_counts

            # 更新MQTT数据缓存
            update_mqtt_cache(view)

        except Exception as e:
            view["errMsg"] = str(e)
        return view

    def get_mqtt_data(self):
        """
        获取真实的MQTT数据
        """
        cache = get_mqtt_cache()

        if cache["latest_data"] is None:
            # 如果没有缓存数据，返回空数据
            return {
                "success": True,
                "data": {
                    "uuid": "no-data",
                    "info": {},
                    "total_detections": 0,
                    "fps": 0,
                    "confidence": 0.0,
                    "line_crossing": {"enter": 0, "exit": 0},
                },
                "message": "暂无MQTT数据",
            }

        # 计算总检测数量
        total_detections = sum(cache["latest_data"]["info"].values())

        # 获取绊线计数
        line_crossing = cache["latest_data"].get(
            "line_crossing", {"enter": 0, "exit": 0}
        )

        # 构建响应数据
        mqtt_data = {
            "uuid": cache["latest_data"]["uuid"],
            "info": cache["latest_data"]["info"],
            "total_detections": total_detections,
            "fps": 0,  # 可以从camera对象获取真实FPS
            "confidence": 0.0,  # 可以从推理结果获取真实置信度
            "line_crossing": line_crossing,
        }

        return {"success": True, "data": mqtt_data, "message": "MQTT数据获取成功"}


class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    mqtt_driver = None
