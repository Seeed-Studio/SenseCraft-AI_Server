import logging
import time
import cv2
from threading import Thread
from ultralytics import YOLO
from output import StreamingOutput


class Camera:
    def __init__(self, output: StreamingOutput, url, modelpath, task):
        self.output = output
        self.url = url
        self.modelpath = modelpath
        self.track = False
        self.predictParams = {}
        self.infering = True
        self.real_fps = None

        self.task = task or "detect"
        """
        task= 'detect', 'segment', 'classify', or 'pose'
        """

        self.reconnect_interval = 1
        """
        reconnect interval, default is 1 seconds
        """

    def __enter__(self):
        self.load_mode()
        if self.mode == "image":
            self.init_image()
        else:
            self.init_stream()
        logging.info(
            "src[{}] fps[{}] width[{}] height[{}] model[{}]".format(
                self.url, self.fps, self.width, self.height, self.modelpath
            )
        )
        self.model = YOLO(self.modelpath, task=self.task)
        self.stop_capture = False
        self.thread = Thread(target=self.capture)
        self.thread.start()
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
        self.cap = cv2.VideoCapture(self.url)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def check_connection_cap(self):
        if not self.cap.isOpened():
            logging.warning("cap lost, reconnecting...")
            self.cap.release()
            time.sleep(self.reconnect_interval)
            self.cap = cv2.VideoCapture(self.url)
        return self.cap

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_capture = True
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
                self.infer(frame)
            self.adjust_fps(start)

    def adjust_fps(self, start):
        """
        adjust and calculate fps by the cost
        """
        cost = time.time() - start
        frame_duration = 1.0 / int(self.fps or 60)  # default: 60fps
        if cost < frame_duration:
            time.sleep(frame_duration - cost)
        real_cost = time.time() - start
        # avg fps with two frame, slow down fps change range, for human easy to see
        fps_new = int(1.0 / real_cost)
        self.real_fps = int(((self.real_fps or fps_new) + fps_new) / 2)

    def handle_end(self):
        """
        when source end or disconnect, replay or reconnect
        """
        if str(self.url).endswith(".mp4"):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if str(self.url).startswith("rtsp://"):
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

    def infer(self, frame):
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
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                **self.predictParams
            )
        else:
            results = self.model.predict(
                frame, device="0", verbose=False, **self.predictParams
            )
        self.output.write(results)
