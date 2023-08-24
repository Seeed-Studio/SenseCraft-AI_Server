sudo docker rm -f edge-gateway-container
sudo docker run -d --privileged \
--restart=always \
--net=host --ipc=bridge --ipc=host --pid=host \
--runtime nvidia --gpus all \
-e EDGEAI_LOG_LEVEL="20" \
-e EDGEAI_MQTT_STARTUP="ON" \
-e EDGEAI_ONLINE="OFF" \
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
--name=edge-gateway-container seeedcloud/edge-gateway:mis-1.0 \
bash -c "python3 /opt/dev/src/main.py"

sudo docker logs edge-gateway-container -f