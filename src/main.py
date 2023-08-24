#!/usr/lib/python3
import logging
import sys
import traceback
import dbus
import dbus.mainloop.glib
import env_helper

sys.path.insert(0, ".")

try:
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    logging.basicConfig(
        stream=sys.stdout,
        level=env_helper.log_level(),
        format="[YOLOv8-MJPEG]%(asctime)s[%(levelname)s] %(pathname)s, line %(lineno)d, => %(message)s",
    )
    numba_logger = logging.getLogger("numba")
    numba_logger.setLevel(logging.WARNING)
    numba_logger = logging.getLogger("werkzeug")
    numba_logger.setLevel(logging.WARNING)
    numba_logger = logging.getLogger("ultralytics")
    numba_logger.setLevel(logging.WARNING)
    logging.info("logging init...")

    if env_helper.is_mqtt_on():
        # if mqtt on
        from mqtt_handler import MqttHandler

        ip, port, user, pwd = env_helper.mqtt_configs()
        MqttHandler(dict(ip=ip, port=port, username=user, password=pwd)).run()
    else:
        # if mqtt off
        from streamer import StreamingHandler, StreamingServer

        server = StreamingServer(env_helper.web_ip_port(), StreamingHandler)
        server.serve_forever()

except KeyboardInterrupt:
    logging.error("manual stop...\n\n")
except Exception as e:
    logging.debug(str(traceback.format_exc()))
    logging.error("Unexception: %s" % str(e))

logging.info("All End...")
