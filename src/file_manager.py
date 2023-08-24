import logging
import mimetypes
import os
import json
import sys
import traceback
from constant import (
    CLOUD_MODEL_CONFIG_URL,
    CLOUD_SAMPLE_VIDEO_URL,
    DEFAULT_MODEL_LIST,
    MODEL_FORMAT_MAP,
)
import env_helper
from utils import download

# default project path
projectPath = os.path.join(os.path.dirname(__file__), "../")

ALLOWED_EXTENSIONS = set(["mp4", "h264", "mov", "avi", "png", "jpg", "jpeg"])


def allowed_source(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


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
        self.sync_cloud_model_list()
        self.prepare_sample()

    def model_list_localfile(self):
        return "{}/{}".format(self.configPath, "cloud-models.json")

    def model_filename(self, modelItem):
        return "{}/{}{}".format(
            self.modelPath,
            modelItem["arguments"]["uuid"],
            MODEL_FORMAT_MAP[modelItem["arguments"]["type"]],
        )

    def task_by_model_id(self, modelId):
        info = self.model_info_by_id(modelId)
        if info:
            return info["arguments"].get("task")
        return None

    def local_model_list(self):
        """
        load local model-configs-file
        - if failed, using hardcode
        """
        if env_helper.online():
            try:
                localModelConfigs = self.model_list_localfile()
                with open(localModelConfigs, "r") as f:
                    cfg = json.load(f)
                return cfg
            except:
                pass
        return DEFAULT_MODEL_LIST

    def sync_cloud_model_list(self):
        """
        try get model list from "seeed open-source model list"
        """
        if env_helper.online():
            try:
                # no matter if download fail
                download(
                    CLOUD_MODEL_CONFIG_URL, self.model_list_localfile(), timeout=10
                )
            except Exception as e:
                logging.error(str(traceback.format_exc()))
                logging.error(str(e))
                logging.error("download {} failed.".format(CLOUD_MODEL_CONFIG_URL))
            self.modelJson = self.local_model_list()
            self.download_all_models()
        self.modelJson = self.local_model_list()
        self.configCache["models"] = json.loads(json.dumps(self.modelJson))

    def prepare_sample(self):
        fileName = "{}/{}".format(self.sourcePath, "sample.mp4")
        self.sampleVideoPath = fileName
        if not os.path.exists(fileName):
            if env_helper.online():
                download(CLOUD_SAMPLE_VIDEO_URL, fileName)
            else:
                logging.error('offline mode: make sure "sources/sample.mp4" existed!!')
                sys.exit(2)

    def model_info_by_id(self, modelId):
        models = self.modelJson["modeList"]
        for modelInfo in models:
            if modelInfo["arguments"]["uuid"] == modelId:
                return modelInfo
        return None

    def get_modelpath(self, modelId):
        info = self.model_info_by_id(modelId)
        if info:
            return self.model_filename(info)
        else:
            return None

    def download_all_models(self):
        """
        base on self.modelJson to download all models
        - depend on local modelJson, so must be called after syncCloudModelList()
        """
        try:
            models = self.modelJson["modeList"]
            for modelInfo in models:
                modelFileName = self.model_filename(modelInfo)
                if not os.path.exists(modelFileName):
                    download(modelInfo["downloadUrl"], modelFileName)
            return True
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
            return False

    def appconfig_path(self):
        return "{}/{}".format(self.configPath, "application.json")

    def get_appConfig(self):
        try:
            with open(self.appconfig_path(), "r") as f:
                self.configCache = json.load(f)
            # manually add 'models' on configs
            self.configCache["models"] = json.loads(json.dumps(self.modelJson))
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
            logging.error("load application.json failed. use default config")
            self.set_appconfig(json.dumps(self.configCache))
        return self.configCache

    def set_appconfig(self, jsonstr):
        """
        save configs, but only for "streams"
        - if failed, still return old configs
        """
        jsonData = json.loads(jsonstr)
        logging.info("=write=> {} ".format(jsonstr))
        if not jsonData.get("streams"):
            # allow empty streams
            self.configCache["streams"] = []
        else:
            self.configCache["streams"] = jsonData["streams"]
        try:
            del self.configCache["models"]
            with open(self.appconfig_path(), "w") as f:
                f.write(json.dumps(self.configCache))
        except Exception as e:
            logging.error(str(traceback.format_exc()))
            logging.error(str(e))
            logging.error("change application.json failed.")
        return self.configCache

    def save_source(self, filename, file_data):
        if not allowed_source(filename):
            raise Exception("Invalid Source Type")
        targetPath = "{}/{}".format(self.sourcePath, filename)
        with open(targetPath, "wb") as f:
            f.write(file_data)
        logging.info("saved: {}".format(targetPath))

    def list_source(self):
        list = os.listdir(self.sourcePath)
        srcList = []
        for filename in list:
            if allowed_source(filename):
                srcList.append(filename)
        return {"list": srcList, "page": 1, "size": len(srcList)}

    def find_source_path(self, src, standard=False):
        """
        - standard=True, only search in sources/+
        - rtsp need special handler because it is not a file, return it
        - if src exists, return it
        - if src in sources/, return its local path
        - if src not found, return sample video path
        """
        # rtsp need special handle
        if str(src).startswith("rtsp://") and not standard:
            return src
        if os.path.exists(src) and not standard:
            return src
        if src in os.listdir(self.sourcePath):
            p = "{}/{}".format(self.sourcePath, src)
            if os.path.exists(p):
                return p
        return self.sampleVideoPath

    def del_source(self, name):
        """
        - only delete files from sources/, besides sample.mp4
        - 1 find in sources/
        - 2 not found, do not delete
        - 3 exists, and not sample.mp4, delete it
        """
        src = self.find_source_path(name, True)
        if src == self.sampleVideoPath:
            return False
        os.remove(src)
        return True

    def get_static(self, path):
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
