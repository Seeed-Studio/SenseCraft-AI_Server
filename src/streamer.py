import datetime
import json
import logging
import socketserver
import traceback
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

fileMgr = FileMgr()


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
            elif self.path == "/syncCloudModel":
                fileMgr.sync_cloud_model_list()
                response = {"message": "sync cloud model ok"}
                self.send_json(response)
                return None
            elif self.path == "/upload":
                try:
                    content_length = int(self.headers["Content-Length"])
                    content_type = self.headers["Content-Type"]
                    boundary = content_type.split("=")[1].encode()
                    filedata = self.rfile.read(content_length)
                    files = parse_files(filedata, boundary)
                    for name in files:
                        filedata = files[name]["data"]
                        filename = files[name]["filename"]
                        fileMgr.save_source(filename, filedata)
                    self.send_html(SOURCE_UPLOAD_HTML)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    self.send_html(str(e))
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
            logging.info(query)
            # TODO: How to be more elegant to deal with this
            if query.get("src"):
                src = fileMgr.find_source_path(query.get("src"))
            if query.get("fps"):
                fps = int(query.get("fps"))
            if query.get("quality"):
                quality = int(query.get("quality"))
            if query.get("model_id"):
                model_id = query.get("model_id")
            if query.get("track"):
                track = int(query.get("track")) > 0
            if query.get("half"):
                half = int(query.get("half")) > 0
            if query.get("conf"):
                conf = float(query.get("conf"))
            if query.get("max_det"):
                max_det = int(query.get("max_det"))
            if query.get("show_box"):
                show_box = int(query.get("show_box")) > 0
            if query.get("uuid"):
                uuid = query.get("uuid")
            if query.get("show_time"):
                show_time = int(query.get("show_time")) > 0
            if query.get("show_fps"):
                show_fps = int(query.get("show_fps")) > 0
            if query.get("infering"):
                infering = int(query.get("infering")) > 0
            if query.get("font_scale"):
                font_scale = int(query.get("font_scale"))
            if query.get("thickness"):
                thickness = int(query.get("thickness"))
            if query.get("txt_color"):
                txt_color = int(query.get("txt_color"))
            if query.get("way"):
                way = int(query.get("way"))
            logging.info(
                "load user config successed. src = {}, fps = {}, quality = {}, model_id = {}, track = {}, half = {}, conf = {}, max_det = {}, show_box = {}, uuid = {}, show_fps = {}, infering = {}".format(
                    src,
                    fps,
                    quality,
                    model_id,
                    track,
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
            if self.path.startswith("/stream"):
                cfg = self.urlparams_load()
                src = cfg["src"]
                fps = cfg["fps"]
                quality = cfg["quality"]
                model_id = cfg["model_id"]
                track = cfg["track"]
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
                    if camera.mode == "stream" and not camera.cap.isOpened():
                        logging.error("Video Source not found.")
                        self.send_html("Video Source not found.", 404)
                        return None
                    else:
                        mqtt_driver = None
                        if env_helper.is_mqtt_on():
                            ip, port, user, pwd = env_helper.mqtt_configs()
                            mqtt_driver = MqttDriver(ip, port, user, pwd)
                        self.send_mjpeg_headers()
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
                                self.send_header("Content-Length", len(frame))
                                self.end_headers()
                                self.wfile.write(frame)
                                self.wfile.write(b"\r\n")
                        except Exception as e:
                            traceback.print_exc()
                            logging.warning(
                                "Removed streaming client {}: {}".format(
                                    self.client_address, str(e)
                                )
                            )
                    return None
            elif self.path.startswith("/appConfigs"):
                response = fileMgr.get_appConfig()
                logging.info(response)
                self.send_json(response)
                return None
            elif self.path.startswith("/about"):
                try:
                    response = about_info()
                    logging.info(response)
                    self.send_json(response)
                except Exception as e:
                    traceback.print_exc()
                    logging.error(str(traceback.format_exc()))
                    logging.error("about Error[{}].".format(str(e)))
                    self.send_html(str(e), 400)
                return None
            elif self.path == "/camList":
                fileMgr.sync_cloud_model_list()
                response = list_freecam()
                self.send_json(response)
                return None
            elif self.path == "/sources/upload":
                self.send_html(SOURCE_UPLOAD_HTML)
                return None
            elif self.path == "/sources/list":
                response = fileMgr.list_source()
                logging.info(response)
                self.send_json(response)
                return None
            elif self.path.startswith("/sources/del"):
                try:
                    query = self.try_get_urlparams()
                    targetName = query.get("name")
                    msg = "del [{}] failed.".format(targetName)
                    if targetName and fileMgr.del_source(targetName):
                        msg = "del [{}] ok".format(targetName)
                    self.send_html(msg)
                except Exception as e:
                    logging.error(str(traceback.format_exc()))
                    self.send_html(str(e), 400)
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
        if content:
            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.end_headers()
            self.wfile.write(content)
            return None
        else:
            logging.error("Error Url Path[{}]".format(self.path))
            self.send_html("Error Url Path[{}]".format(self.path), 404)
        return None

    def send_html(self, html: str = None, code=200):
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
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
        self.end_headers()

    def get_one_frame(
        self,
        camera: Camera,
        mqtt_driver: MqttDriver,
        fps,
        quality,
        uuid,
        show_box,
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
            result = camera.output.results[0]
            rawFrame = camera.output.orig_img
            if not camera.infering and rawFrame is not None:
                img = img_copy(rawFrame)
            else:
                if env_helper.is_mqtt_on():
                    viewInfo = self.handle_view_info(result, uuid)
                    mqtt_driver.publish(RESULT_TOPIC, json.dumps(viewInfo))
                img = result.plot(boxes=show_box)
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
            resObj = json.loads(result.tojson())
            for obj in resObj:
                if view["info"].get(obj["name"]):
                    view["info"][obj["name"]] += 1
                else:
                    view["info"][obj["name"]] = 1
        except Exception as e:
            view["errMsg"] = str(e)
        return view


class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    mqtt_driver = None
