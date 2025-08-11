#!/bin/bash
# docker build -t scas . # only for first time
# IMAGE=ultralytics/ultralytics:latest-jetson-jetpack6
IMAGE=scas
# start new contaniner, mount project's files
docker rm -f edge-gateway-container
docker run -it --rm --privileged \
--net=host --ipc=bridge --ipc=host --pid=host \
--runtime nvidia --gpus all \
-e EDGEAI_LOG_LEVEL="20" \
-e EDGEAI_MQTT_STARTUP="ON" \
-e EDGEAI_MQTT_IP="172.17.0.1" \
-e EDGEAI_MQTT_PORT="1883" \
-e EDGEAI_MODELS_PATH="/opt/dev/models/" \
-e EDGEAI_SOURCES_PATH="/opt/dev/sources/" \
-e EDGEAI_CONFIGS_PATH="/opt/dev/configs/" \
-e EDGEAI_WEB_DIST_PATH="/opt/dev/dist/" \
-e EDGEAI_PORT="46654" \
-v $PWD/models:/opt/dev/models/ \
-v $PWD/configs:/opt/dev/configs/ \
-v $PWD/sources:/opt/dev/sources/ \
-v $PWD/dist:/opt/dev/dist/ \
-v $PWD/src:/opt/dev/src/ \
-v /dev:/dev -v /tmp/.X11-unix/:/tmp/.X11-unix \
-v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket \
--name=edge-gateway-container $IMAGE bash # -c "python3 /opt/dev/src/main.py"