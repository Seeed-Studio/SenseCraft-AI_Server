#!/bin/bash

# 测试run.sh脚本的功能（不实际启动容器）

echo "=== 测试SenseCraft AI Server启动脚本 ==="

# 设置镜像名称
IMAGE=scas

echo "1. 检查Docker镜像 $IMAGE..."
if [[ "$(docker images -q $IMAGE 2> /dev/null)" == "" ]]; then
    echo "镜像 $IMAGE 不存在，需要构建"
    echo "测试构建命令：docker build -t $IMAGE ."
else
    echo "✅ 镜像 $IMAGE 已存在"
fi

echo ""
echo "2. 检查MQTT服务（端口1883）..."
if netstat -tuln | grep -q ":1883 "; then
    echo "✅ MQTT服务正在运行（端口1883）"
else
    echo "⚠️  MQTT服务未运行（端口1883）"
    echo "建议启动MQTT服务："
    echo "  ./scripts/mqtt.sh start"
fi

echo ""
echo "3. 检查Docker容器状态..."
if docker ps -a | grep -q "edge-gateway-container"; then
    echo "发现现有容器："
    docker ps -a | grep "edge-gateway-container"
    echo "容器清理命令：sudo docker rm -f edge-gateway-container"
else
    echo "✅ 没有发现现有容器"
fi

echo ""
echo "4. 检查必要的目录和文件..."
directories=("models" "sources" "configs" "dist" "src")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ 目录 $dir 存在"
    else
        echo "❌ 目录 $dir 不存在"
    fi
done

echo ""
echo "5. 检查Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile 存在"
else
    echo "❌ Dockerfile 不存在"
fi

echo ""
echo "=== 测试完成 ==="
echo ""
echo "如果所有检查都通过，可以运行："
echo "  bash scripts/run.sh"
echo ""
echo "如果MQTT服务未运行，先启动："
echo "  ./scripts/mqtt.sh start" 