FROM ultralytics/ultralytics:latest-jetson-jetpack6

# 安装 GStreamer 插件和 FFmpeg（用于硬件加速）
# 注意：NVDEC 支持通常已包含在 ultralytics/ultralytics:latest-jetson-jetpack6 基础镜像中
RUN apt update && apt install -y \
    python3-dbus \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 验证硬件加速支持
RUN echo "=== 检查硬件加速支持 ===" && \
    (gst-inspect-1.0 nvdec 2>/dev/null && echo "✅ GStreamer NVDEC plugin found" || echo "⚠️  GStreamer NVDEC plugin not found") && \
    (ffmpeg -hide_banner -hwaccels 2>/dev/null | grep -q nvdec && echo "✅ FFmpeg NVDEC support found" || echo "⚠️  FFmpeg NVDEC support not found") && \
    echo "========================="

# 安装 Python 依赖
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

# GStreamer 环境变量（用于硬件加速）
# GST_DEBUG: 0=无, 1=错误, 2=警告, 3=修复, 4=信息, 5=调试, 6=跟踪
# 如需调试 GStreamer，可在 run.sh 中设置 GST_DEBUG=5
ENV GST_DEBUG=1
ENV GST_DEBUG_NO_COLOR=1
ENV GST_PLUGIN_PATH=/usr/lib/aarch64-linux-gnu/gstreamer-1.0

CMD [ "python3", "src/main.py", " 2>/dev/null" ]
