FROM ultralytics/ultralytics:latest-jetson-jetpack6
RUN apt update && apt install -y python3-dbus
RUN pip install paho-mqtt lapx

WORKDIR /opt/dev/

COPY ./models /opt/dev/models
COPY ./sources /opt/dev/sources
COPY ./configs /opt/dev/configs
COPY ./src /opt/dev/src

ENV EDGEAI_LOG_LEVEL="20"
ENV EDGEAI_MQTT_STARTUP="ON"
ENV EDGEAI_MODELS_PATH="/opt/dev/models"
ENV EDGEAI_SOURCES_PATH="/opt/dev/sources"
ENV EDGEAI_CONFIGS_PATH="/opt/dev/configs"
ENV EDGEAI_WEB_DIST_PATH="/opt/dev/dist"
ENV EDGEAI_PORT="46654"
ENV EDGEAI_MQTT_USER="seeed"
ENV EDGEAI_MQTT_PWD="BP6Y6XT4PvE4"

CMD [ "python3", "src/main.py", " 2>/dev/null" ]
