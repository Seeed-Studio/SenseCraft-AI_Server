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
        MqttHandler.init_flag = True

    def __del__(self):
        """析构函数，确保清理资源"""
        try:
            self.cleanup()
        except Exception as e:
            logging.debug(f"MqttHandler清理时出现异常（可忽略）: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        logging.debug(
            "on_connect[{}:{}] {} {} {} {} {}".format(
                self.broker, self.port, client, userdata, flags, reason_code, properties
            )
        )
        if reason_code == 0:
            logging.debug("connected, sub: {}".format(self.sub_topics))
            for topic in self.sub_topics:
                self.client.subscribe(topic)
            # mjpeg server startup
            self.start_streamserver()
        else:
            logging.error("on_connect failed: %d\n", reason_code)

    def start_streamserver(self):
        try:
            self.server = StreamingServer(env_helper.web_ip_port(), StreamingHandler)
            self.server.mqtt_driver = self
            self.server.serve_forever()
        except Exception as e:
            logging.error(f"启动流媒体服务器失败: {e}")

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            rawMsg = message.payload.decode()
            logging.debug(f"recv `{rawMsg}` from `{topic}`")
            if topic == CMD_TOPIC:
                logging.info(f"recv `{rawMsg}` from `{topic}`")
            else:
                logging.debug("unhandler topic: %s" % topic)
        except Exception as e:
            logging.error(f"处理MQTT消息时出错: {e}")

    def run(self):
        logging.info("mqtt client run... {}".format(self.broker))
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info("收到停止信号，正在关闭MQTT客户端...")
        except Exception as e:
            logging.error(f"MQTT客户端运行出错: {e}")
        finally:
            self.cleanup()
