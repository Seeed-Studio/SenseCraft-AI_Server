#!/usr/lib/python3
import logging
import threading
from constant import CMD_TOPIC
from streamer import StreamingHandler, StreamingServer
from mqtt_driver import MqttDriver
import env_helper


class MqttHandler(MqttDriver):
    instance = None
    init_flag = False
    run_flag = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        logging.debug("__new__ {} {} {}".format(cls, args, kwargs))
        if cls.instance:
            return cls.instance
        with cls._lock:
            if cls.instance is None:
                cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(
        self, options: dict = {"ip": "", "port": 0, "username": "", "password": ""}
    ):
        if MqttHandler.init_flag:
            logging.debug("MqttClient already init...")
            return
        logging.debug("MqttClient init...")
        # init mqttDriver first, otherwise reload the 'sub_topics' values
        MqttDriver.__init__(
            self,
            options["ip"],
            options["port"],
            options["username"],
            options["password"],
        )
        self.sub_topics = [CMD_TOPIC]
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        logging.debug(
            "on_connect[{}:{}] {} {} {} {}".format(
                self.broker, self.port, client, userdata, flags, rc
            )
        )
        if rc == 0:
            logging.debug("connected, sub: {}".format(self.sub_topics))
            for topic in self.sub_topics:
                self.client.subscribe(topic)
            # mjpeg server startup
            self.start_streamserver()
        else:
            logging.error("on_connect failed: %d\n", rc)

    def start_streamserver(self):
        self.server = StreamingServer(env_helper.web_ip_port(), StreamingHandler)
        self.server.mqtt_driver = self
        self.server.serve_forever()

    def on_message(self, client, userdata, message):
        topic = message.topic
        rawMsg = message.payload.decode()
        logging.debug(f"recv `{rawMsg}` from `{topic}`")
        if topic == CMD_TOPIC:
            logging.info(f"recv `{rawMsg}` from `{topic}`")
        else:
            logging.debug("unhandler topic: %s" % topic)

    def run(self):
        logging.info("mqtt client run... {}".format(self.broker))
        self.client.loop_forever()
