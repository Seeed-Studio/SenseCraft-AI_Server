#!/bin/bash

echo "🚀 启动SenseCraft AI Server (MQTT模式)"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  安装requests依赖..."
    pip3 install requests
fi

# 启动服务器
echo "🔧 启动服务器..."
echo "📡 MQTT数据接口: http://localhost:46654/mqtt/data"
echo "🌐 Web界面: http://localhost:46654"
echo ""

# 设置环境变量
export EDGEAI_LOG_LEVEL="20"
export EDGEAI_MQTT_STARTUP="OFF"  # 关闭真实MQTT，使用模拟数据
export EDGEAI_PORT="46654"

# 启动服务器
python3 src/main.py &
SERVER_PID=$!

# 等待服务器启动
echo "⏳ 等待服务器启动..."
sleep 3

# 检查服务器是否启动成功
if curl -s http://localhost:46654 > /dev/null; then
    echo "✅ 服务器启动成功!"
    echo ""
    echo "🧪 运行MQTT测试..."
    python3 test_mqtt.py
    echo ""
    echo "🌐 打开浏览器访问: http://localhost:46654"
    echo "📡 在Web界面中点击'开始监听'按钮查看MQTT数据"
    echo ""
    echo "按 Ctrl+C 停止服务器"
    
    # 等待用户中断
    wait $SERVER_PID
else
    echo "❌ 服务器启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi 