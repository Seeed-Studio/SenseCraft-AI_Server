import logging
import os

EDGEAI_MQTT_IP = 1
EDGEAI_MQTT_PORT = 2
EDGEAI_LOG_LEVEL = 3
EDGEAI_MQTT_STARTUP = 4
EDGEAI_IP = 5
EDGEAI_PORT = 6
EDGEAI_MODELS_PATH = 7
EDGEAI_SOURCES_PATH = 8
EDGEAI_CONFIGS_PATH = 9
EDGEAI_WEB_DIST_PATH = 10
EDGEAI_MQTT_USER = 11
EDGEAI_MQTT_PWD = 12
EDGEAI_ONLINE = 13
# TODO: maybe using config.ini is better
ENV_NAME = {
    EDGEAI_MQTT_IP: "EDGEAI_MQTT_IP",
    EDGEAI_MQTT_PORT: "EDGEAI_MQTT_PORT",
    EDGEAI_LOG_LEVEL: "EDGEAI_LOG_LEVEL",
    EDGEAI_MQTT_STARTUP: "EDGEAI_MQTT_STARTUP",
    EDGEAI_IP: "EDGEAI_IP",
    EDGEAI_PORT: "EDGEAI_PORT",
    EDGEAI_MODELS_PATH: "EDGEAI_MODELS_PATH",
    EDGEAI_SOURCES_PATH: "EDGEAI_SOURCES_PATH",
    EDGEAI_CONFIGS_PATH: "EDGEAI_CONFIGS_PATH",
    EDGEAI_WEB_DIST_PATH: "EDGEAI_WEB_DIST_PATH",
    EDGEAI_MQTT_USER: "EDGEAI_MQTT_USER",
    EDGEAI_MQTT_PWD: "EDGEAI_MQTT_PWD",
    EDGEAI_ONLINE: "EDGEAI_ONLINE",
}


def online():
    if os.environ.get(ENV_NAME[EDGEAI_ONLINE]) == "ON":
        return True
    return False


def models_dir():
    return os.environ.get(ENV_NAME[EDGEAI_MODELS_PATH])


def sources_dir():
    return os.environ.get(ENV_NAME[EDGEAI_SOURCES_PATH])


def configs_dir():
    return os.environ.get(ENV_NAME[EDGEAI_CONFIGS_PATH])


def web_dist_dir():
    return os.environ.get(ENV_NAME[EDGEAI_WEB_DIST_PATH])


def mqtt_configs():
    MQTT_IP = "127.0.0.1"
    MQTT_PORT = 1883
    env_ip = os.environ.get(ENV_NAME[EDGEAI_MQTT_IP])
    env_port = os.environ.get(ENV_NAME[EDGEAI_MQTT_PORT])
    if env_ip:
        MQTT_IP = env_ip
    if env_port:
        MQTT_PORT = env_port

    USERNAME = "seeed"
    PASSWORD = "BP6Y6XT4PvE4"
    env_user = os.environ.get(ENV_NAME[EDGEAI_MQTT_USER])
    env_pwd = os.environ.get(ENV_NAME[EDGEAI_MQTT_PWD])
    if env_user:
        USERNAME = env_user
    if env_pwd:
        PASSWORD = env_pwd

    return (
        MQTT_IP,
        MQTT_PORT,
        USERNAME,
        PASSWORD,
    )


def log_level():
    """
    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    """
    LEVEL = logging.INFO
    env_loglevel = os.environ.get(ENV_NAME[EDGEAI_LOG_LEVEL])
    try:
        if env_loglevel:
            LEVEL = int(env_loglevel)
    except:
        pass
    return LEVEL


def is_mqtt_on():
    """
    if EDGEAI_MQTT_STARTUP != "OFF", mqtt functions working.
    """
    if os.environ.get(ENV_NAME[EDGEAI_MQTT_STARTUP]) != "OFF":
        return True
    return False


def web_ip_port():
    """
    web server's configs
    - default ip ""
    - default port 46654
    """
    env_ip = os.environ.get(ENV_NAME[EDGEAI_IP])
    env_port = os.environ.get(ENV_NAME[EDGEAI_PORT])
    return (env_ip or "", int(env_port or 46654))


def my_version():
    return "v0.0.1"
