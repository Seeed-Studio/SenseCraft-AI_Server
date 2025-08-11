#!/usr/lib/python3
import logging
import random
from time import sleep
from paho.mqtt import client as mqtt_client
import traceback

class MqttDriver:
    """basic mqtt driver"""

    def __init__(self, ip, port, username=None, passwd=None):
        logging.debug("MqttDriver init... {} {}".format(ip, port))
        self.broker = ip
        # 确保端口号是整数类型
        self.port = int(port) if isinstance(port, str) else port
        # create mqttClient with VERSION2 callback API
        self.client = mqtt_client.Client(
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
        )
        if username is not None and passwd is not None:
            self.client.username_pw_set(username, passwd)

        self.sub_topics = []
        self._connected = False

        # standard handler
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        # create connection
        try:
            self.client.connect(self.broker, self.port)
            self._connected = True
        except Exception as e:
            logging.warning(f"MQTT连接失败: {e}")
            logging.error(str(traceback.format_exc()))
            self._connected = False

    def __del__(self):
        """析构函数，安全清理MQTT客户端"""
        self.cleanup()

    def cleanup(self):
        """安全清理MQTT连接"""
        try:
            if hasattr(self, 'client') and self.client:
                if self._connected:
                    self.client.disconnect()
                self.client.loop_stop()
                # 防止析构时的AttributeError
                if hasattr(self.client, '_sock'):
                    self.client._sock = None
        except Exception as e:
            logging.debug(f"MQTT清理时出现异常（可忽略）: {e}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logging.debug("on_disconnect... {} {} {} {} {}".format(userdata, self.broker, flags, reason_code, properties))
        self._connected = False

    def on_connect(self, client, userdata, flags, reason_code, properties):
        raise Exception("on_connect must be reload.")

    def on_message(self, client, userdata, msg):
        logging.debug(f"recv msg `{msg.payload.decode()}` from `{msg.topic}`")
        raise Exception("on_message must be reload.")

    msg_count = 1

    def publish(self, topic, msg):
        """
        basic publish with counter
        """
        if not self._connected:
            logging.warning("MQTT未连接，无法发布消息")
            return
            
        result = self.client.publish(topic, msg, 0, False)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            logging.debug(f"No.{self.msg_count} msg send ok: `{msg}` to `{topic}`")
        else:
            logging.error(f"No.{self.msg_count} msg send failed: `{msg}` to `{topic}`")
        self.msg_count += 1
        sleep(0.001)
