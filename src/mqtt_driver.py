#!/usr/lib/python3
import logging
import random
from time import sleep
from paho.mqtt import client as mqtt_client


class MqttDriver:
    """basic mqtt driver"""

    def __init__(self, ip, port, username=None, passwd=None):
        logging.debug("MqttDriver init... {} {}".format(ip, port))
        self.broker = ip
        self.port = port
        # generate client ID with pub prefix randomly
        self.client_id = f"python-mqtt-{random.randint(0, 1000)}"
        # create mqttClient
        self.client = mqtt_client.Client(self.client_id)
        if username is not None and passwd is not None:
            self.client.username_pw_set(username, passwd)

        self.sub_topics = []

        # standard handler
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        # create connection
        self.client.connect(self.broker, self.port)

    def on_disconnect(self, userdata, flags, rc):
        logging.debug("on_disconnect... {} {} {}".format(userdata, self.broker, rc))

    def on_connect(self, client, userdata, flags, rc):
        raise Exception("on_connect must be reload.")

    def on_message(self, client, userdata, msg):
        logging.debug(f"recv msg `{msg.payload.decode()}` from `{msg.topic}`")
        raise Exception("on_message must be reload.")

    msg_count = 1

    def publish(self, topic, msg):
        """
        basic publish with counter
        """
        result = self.client.publish(topic, msg, 0, False)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            logging.debug(f"No.{self.msg_count} msg send ok: `{msg}` to `{topic}`")
        else:
            logging.error(f"No.{self.msg_count} msg send failed: `{msg}` to `{topic}`")
        self.msg_count += 1
        sleep(0.001)
