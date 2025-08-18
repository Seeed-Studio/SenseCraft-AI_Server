#!/bin/bash

# 设置镜像名称
IMAGE_NAME=scas
IMAGE=${IMAGE_NAME}:latest

echo "=== SenseCraft AI Server 启动脚本 ==="

# 检测镜像是否存在
echo "检查Docker镜像 $IMAGE..."
if [[ "$(docker images -q $IMAGE 2> /dev/null)" == "" ]]; then
    echo "镜像 $IMAGE 不存在，开始构建..."
    echo "构建可能需要几分钟时间，请耐心等待..."
    docker build -t $IMAGE .
    if [ $? -eq 0 ]; then
        echo "✅ 镜像构建成功！"
    else
        echo "❌ 镜像构建失败！"
        exit 1
    fi
else
    echo "✅ 镜像 $IMAGE 已存在"
    # 生成时间戳标签保存当前版本
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_TAG=${IMAGE_NAME}:backup_${TIMESTAMP}
    
    echo "📦 备份当前镜像为: $BACKUP_TAG"
    docker tag $IMAGE $BACKUP_TAG
    
    echo "🔄 重新构建最新版本..."
    echo "构建可能需要几分钟时间，请耐心等待..."
    docker build -t $IMAGE .
    
    if [ $? -eq 0 ]; then
        echo "✅ 新版本镜像构建成功！"
        echo "📋 当前版本: $IMAGE" 
        echo "📋 备份版本: $BACKUP_TAG"
    else
        echo "❌ 镜像构建失败！"
        exit 1
    fi
fi

# 检测MQTT服务是否运行
echo "检查MQTT服务（端口1883）..."
if netstat -tuln | grep -q ":1883 "; then
    echo "✅ MQTT服务正在运行（端口1883）"
else
    echo "⚠️  MQTT服务未运行（端口1883）"
    echo "建议启动MQTT服务以确保完整功能："
    echo "  sudo systemctl start mosquitto"
    echo "  sudo systemctl enable mosquitto"
    echo "继续启动AI服务器..."
fi

# 移除旧容器（如果存在）
echo "清理旧容器..."
sudo docker rm -f edge-gateway-container 2>/dev/null || true

# 启动新容器
echo "启动SenseCraft AI Server容器..."
sudo docker run -d --privileged \
--restart=always \
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
--name=edge-gateway-container $IMAGE \
bash -c "python3 /opt/dev/src/main.py"

# 检查容器启动状态
if [ $? -eq 0 ]; then
    echo "✅ SenseCraft AI Server 启动成功！"
    echo ""
    echo "🌐 访问Web界面："
    echo "   本机访问: http://localhost:46654/"
    echo "   远程访问: http://$(hostname -I | awk '{print $1}'):46654/"
    echo ""
    echo "📊 查看运行日志："
    echo "   sudo docker logs edge-gateway-container -f"
    echo ""
    echo "🛑 停止服务："
    echo "   sudo docker stop edge-gateway-container"
    echo ""
    echo "正在显示启动日志..."
    echo "按 Ctrl+C 退出日志查看（服务将继续运行）"
    echo "=================================="
    
    # 显示日志
    sudo docker logs edge-gateway-container -f
else
    echo "❌ SenseCraft AI Server 启动失败！"
    echo "请检查错误信息并重试"
    exit 1
fi