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
    logging.info("=== SenseCraft AI Server 启动中 ===")
    logging.info("日志系统初始化完成...")

    if env_helper.is_mqtt_on():
        # if mqtt on
        logging.info("MQTT模式启动中...")
        from mqtt_handler import MqttHandler

        ip, port, user, pwd = env_helper.mqtt_configs()
        logging.info("MQTT配置: IP={}, Port={}, User={}".format(ip, port, user))
        MqttHandler(dict(ip=ip, port=port, username=user, password=pwd)).run()
    else:
        # if mqtt off
        logging.info("HTTP服务器模式启动中...")
        from streamer import StreamingHandler, StreamingServer

        server_ip, server_port = env_helper.web_ip_port()
        server = StreamingServer((server_ip, server_port), StreamingHandler)
        
        # 打印服务器启动信息
        if server_ip:
            server_url = "http://{}:{}".format(server_ip, server_port)
        else:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            server_url = "http://{}:{}".format(local_ip, server_port)
        
        logging.info("=" * 60)
        logging.info("🎉 SenseCraft AI Server 启动成功!")
        logging.info("📡 服务器地址: {}".format(server_url))
        logging.info("🔧 端口: {}".format(server_port))
        logging.info("📁 模型路径: {}".format(env_helper.models_dir()))
        logging.info("📁 源文件路径: {}".format(env_helper.sources_dir()))
        logging.info("📁 配置文件路径: {}".format(env_helper.configs_dir()))
        logging.info("🌐 版本: {}".format(env_helper.my_version()))
        logging.info("=" * 60)
        logging.info("🚀 服务器正在运行，等待连接...")
        
        server.serve_forever()

except KeyboardInterrupt:
    logging.info("收到停止信号，正在关闭服务器...")
    logging.error("手动停止...\n\n")
except Exception as e:
    logging.debug(str(traceback.format_exc()))
    logging.error("未预期的错误: %s" % str(e))

logging.info("服务器已关闭，程序结束...")
