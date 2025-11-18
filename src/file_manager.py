import logging
import mimetypes
import os
import json
import sys
import traceback
from uuid import uuid4
import env_helper

# default project path
projectPath = os.path.join(os.path.dirname(__file__), "../")

ALLOWED_EXTENSIONS = set(["mp4", "h264", "mov", "avi", "png", "jpg", "jpeg"])


def allowed_source(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


STREAM_FIELD_DEFAULTS = {
    "name": "默认流",
    "enabled": True,
    "src": "sample.mp4",
    "model_id": "",
    "conf": "0.25",
    "max_det": "300",
    "half": "0",
    "show_fps": "1",
    "show_time": "1",
    "show_box": "1",
    "box_color": "orange",
    "track": "1",
    "show_trail": "1",
    "trail_length": "50",
    "trail_thickness": "2",
    "trail_color": "blue",
    # 是否启用诊断信息（处理帧率/推理时长等）
    "enable_diagnostics": "1",
    # 推理分辨率（传给 ultralytics 的 imgsz），为空则使用模型默认
    "imgsz": "",
}

STREAM_FIELD_ORDER = [
    "src",
    "model_id",
    "conf",
    "max_det",
    "half",
    "show_fps",
    "show_time",
    "show_box",
    "box_color",
    "track",
    "show_trail",
    "trail_length",
    "trail_thickness",
    "trail_color",
    "enable_diagnostics",
    "imgsz",
]


class FileMgr:
    def __init__(self) -> None:
        # default configs
        self.configCache = {"streams": []}
        self.modelPath = env_helper.models_dir() or (projectPath + "models")
        if not os.path.exists(self.modelPath):
            os.makedirs(self.modelPath)
        self.configPath = env_helper.configs_dir() or (projectPath + "configs")
        if not os.path.exists(self.configPath):
            os.makedirs(self.configPath)
        self.sourcePath = env_helper.sources_dir() or (projectPath + "sources")
        if not os.path.exists(self.sourcePath):
            os.makedirs(self.sourcePath)
        self.staticPath = env_helper.web_dist_dir() or (projectPath + "dist")
        if not os.path.exists(self.staticPath):
            os.makedirs(self.staticPath)
        
        # 初始化模型列表
        self.init_model_list()
        self.prepare_sample()

    def init_model_list(self):
        """
        初始化模型列表 - 从本地目录扫描模型文件
        """
        self.modelJson = self.scan_local_models()
        self.configCache["models"] = json.loads(json.dumps(self.modelJson))
        logging.info("📁 扫描到 {} 个本地模型".format(len(self.modelJson["modeList"])))

    def scan_local_models(self):
        """
        扫描本地models目录，自动发现模型文件
        """
        model_list = {
            "versionCode": 0,
            "versionName": "0.0.0",
            "updatedAt": 0,
            "modeList": []
        }
        
        if not os.path.exists(self.modelPath):
            logging.warning("模型目录不存在: {}".format(self.modelPath))
            return model_list
        
        # 扫描模型文件
        for filename in os.listdir(self.modelPath):
            file_path = os.path.join(self.modelPath, filename)
            if os.path.isfile(file_path):
                # 根据文件扩展名判断模型类型
                model_info = self.create_model_info(filename, file_path)
                if model_info:
                    model_list["modeList"].append(model_info)
                    logging.info("📋 发现模型: {} - {}".format(model_info["name"], filename))
        
        return model_list

    def create_model_info(self, filename, file_path):
        """
        根据文件名创建模型信息
        """
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 根据扩展名判断模型类型
        if filename.endswith('.engine'):
            model_type = "TensorRT"
            task = "detect"
            model_id = filename.replace('.engine', '')
        elif filename.endswith('.pt'):
            model_type = "PyTorch"
            task = "detect"
            model_id = filename.replace('.pt', '')
        elif filename.endswith('.onnx'):
            model_type = "ONNX"
            task = "detect"
            model_id = filename.replace('.onnx', '')
        else:
            # 未知格式，跳过
            return None
        
        return {
            "downloadUrl": "",  # 本地模型，不需要下载URL
            "name": "{} ({})".format(model_id, model_type),
            "size": file_size,
            "icon": "",  # 本地模型，不需要图标URL
            "arguments": {
                "uuid": model_id,
                "type": model_type,
                "task": task,
                "half": False,
            }
        }

    def task_by_model_id(self, modelId):
        info = self.model_info_by_id(modelId)
        if info:
            return info["arguments"].get("task")
        return None

    def model_info_by_id(self, modelId):
        models = self.modelJson["modeList"]
        for modelInfo in models:
            if modelInfo["arguments"]["uuid"] == modelId:
                return modelInfo
        return None
    
    def s_model_path(self, name):
        """
        获取模型文件路径 - 直接使用文件名
        """
        return os.path.join(self.modelPath, name)

    def get_modelpath(self, modelId):
        """
        根据模型ID获取模型文件路径
        """
        info = self.model_info_by_id(modelId)
        if info:
            # 根据模型类型构建文件名
            model_type = info["arguments"]["type"]
            if model_type == "TensorRT":
                filename = "{}.engine".format(modelId)
            elif model_type == "PyTorch":
                filename = "{}.pt".format(modelId)
            elif model_type == "ONNX":
                filename = "{}.onnx".format(modelId)
            else:
                filename = modelId
            
            return os.path.join(self.modelPath, filename)
        else:
            return None

    def prepare_sample(self):
        """
        准备示例视频文件
        """
        fileName = os.path.join(self.sourcePath, "sample.mp4")
        self.sampleVideoPath = fileName
        if not os.path.exists(fileName):
            logging.error('请确保 "sources/sample.mp4" 文件存在!')
            logging.info('您可以将任何MP4视频文件重命名为 sample.mp4 并放入 sources/ 目录')

    def appconfig_path(self):
        return os.path.join(self.configPath, "application.json")

    def get_appConfig(self):
        try:
            with open(self.appconfig_path(), "r") as f:
                loaded_config = json.load(f)
                # 更新配置缓存，保留现有字段
                self.configCache.update(loaded_config)
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
            logging.error("加载 application.json 失败，使用默认配置")
        finally:
            self._ensure_streams(self.configCache)
            # 添加模型信息到配置中（每次获取时都更新）
            self.configCache["models"] = json.loads(json.dumps(self.modelJson))
        return self.configCache

    def set_appconfig(self, jsonstr):
        """
        保存配置，保存前端发送的所有配置字段
        """
        jsonData = json.loads(jsonstr)
        logging.info("保存配置: {}".format(jsonstr))
        
        # 更新配置缓存，保存所有前端发送的字段
        self.configCache.update(jsonData)
        self._ensure_streams(self.configCache)
        
        try:
            # 移除models部分，避免保存到文件
            if "models" in self.configCache:
                del self.configCache["models"]
            with open(self.appconfig_path(), "w") as f:
                f.write(json.dumps(self.configCache, indent=2, ensure_ascii=False))
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
            logging.error("保存 application.json 失败")
        return self.configCache

    def save_source(self, filename, file_data):
        if not allowed_source(filename):
            raise Exception("无效的源文件类型")
        targetPath = os.path.join(self.sourcePath, filename)
        with open(targetPath, "wb") as f:
            f.write(file_data)
        logging.info("保存源文件: {}".format(targetPath))

    def save_model(self, filename, file_data):
        """保存模型文件"""
        # 检查文件扩展名
        allowed_model_extensions = {'.pt', '.pth', '.onnx', '.engine'}
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_model_extensions:
            raise Exception("无效的模型文件类型，支持: {}".format(', '.join(allowed_model_extensions)))
        
        targetPath = os.path.join(self.modelPath, filename)
        with open(targetPath, "wb") as f:
            f.write(file_data)
        logging.info("保存模型文件: {}".format(targetPath))
        
        # 重新扫描模型列表
        self.init_model_list()

    def list_source(self):
        """
        列出所有源文件
        """
        if not os.path.exists(self.sourcePath):
            return {"list": [], "page": 1, "size": 0}
        
        file_list = os.listdir(self.sourcePath)
        srcList = []
        for filename in file_list:
            if allowed_source(filename):
                srcList.append(filename)
        return {"list": srcList, "page": 1, "size": len(srcList)}

    def list_models(self):
        """
        列出所有可用模型
        """
        if not os.path.exists(self.modelPath):
            return {"list": [], "page": 1, "size": 0}
        
        model_list = []
        for filename in os.listdir(self.modelPath):
            file_path = os.path.join(self.modelPath, filename)
            if os.path.isfile(file_path):
                model_info = self.create_model_info(filename, file_path)
                if model_info:
                    # 添加文件路径信息
                    model_info["file_path"] = file_path
                    model_info["filename"] = filename
                    model_list.append(model_info)
        
        return {"list": model_list, "page": 1, "size": len(model_list)}

    def find_source_path(self, src, standard=False):
        """
        查找源文件路径
        - standard=True, 只在 sources/ 目录中搜索
        - rtsp 需要特殊处理，因为它不是文件，直接返回
        - 如果 src 存在，返回它
        - 如果 src 在 sources/ 中，返回其本地路径
        - 如果 src 未找到，返回示例视频路径
        """
        # rtsp 需要特殊处理
        if str(src).startswith("rtsp://") and not standard:
            return src
        if os.path.exists(src) and not standard:
            return src
        if src in os.listdir(self.sourcePath):
            p = os.path.join(self.sourcePath, src)
            if os.path.exists(p):
                return p
        return self.sampleVideoPath

    def del_source(self, name):
        """
        删除源文件
        - 只删除 sources/ 目录中的文件，除了 sample.mp4
        """
        src = self.find_source_path(name, True)
        if src == self.sampleVideoPath:
            return False
        os.remove(src)
        return True

    def del_model(self, name):
        """
        删除模型文件
        """
        model_path = os.path.join(self.modelPath, name)
        if os.path.exists(model_path):
            os.remove(model_path)
            # 重新扫描模型列表
            self.init_model_list()
            return True
        return False

    def get_static(self, path):
        """
        获取静态文件
        """
        staticfile = path.lstrip("/")
        if str(path).find("?") != -1:
            staticfile = staticfile.split("?")[0]
        file_path = os.path.join(self.staticPath, staticfile)
        mime_type, _ = mimetypes.guess_type(file_path)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
                return (mime_type, content)
        return (mime_type, None)

    def _ensure_streams(self, config):
        """
        确保 streams 字段存在并补全默认值，同时保持向后兼容
        """
        streams = config.get("streams")
        if not isinstance(streams, list):
            streams = []

        if not streams:
            # 旧版本配置迁移：将顶层字段转换为一个流
            fallback_stream = {}
            for key in STREAM_FIELD_ORDER:
                if config.get(key) is not None:
                    fallback_stream[key] = str(config.get(key))
            streams = [self._build_stream_defaults(fallback_stream, index=0)]
        else:
            normalized = []
            for idx, stream in enumerate(streams):
                normalized.append(self._build_stream_defaults(stream or {}, idx))
            streams = normalized

        config["streams"] = streams

        # 激活流 ID
        active_id = config.get("active_stream_id")
        if active_id not in [s["id"] for s in streams]:
            active_id = streams[0]["id"]
        config["active_stream_id"] = active_id
        primary_stream = next((s for s in streams if s["id"] == active_id), streams[0])

        # 将主流字段同步到顶层，兼容旧逻辑
        for key in STREAM_FIELD_ORDER:
            config[key] = primary_stream.get(key, STREAM_FIELD_DEFAULTS.get(key))

    def _build_stream_defaults(self, data, index=0):
        stream = STREAM_FIELD_DEFAULTS.copy()
        stream.update({k: str(v) if isinstance(v, (int, float)) else v for k, v in data.items() if v is not None})
        if not stream.get("id"):
            stream["id"] = f"stream-{uuid4().hex[:8]}"
        if not stream.get("name"):
            stream["name"] = f"流{index + 1}"
        stream["enabled"] = bool(stream.get("enabled", True))
        return stream

    def stream_by_id(self, stream_id: str | None):
        if not stream_id:
            return None
        config = self.get_appConfig()
        for stream in config.get("streams", []):
            if stream.get("id") == stream_id:
                return stream
        return None
