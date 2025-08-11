#!/bin/bash

# MQTT服务管理脚本

MQTT_SERVICE="mosquitto"
MQTT_PORT="1883"

echo "=== MQTT服务管理脚本 ==="

case "$1" in
    start)
        echo "启动MQTT服务..."
        sudo systemctl start $MQTT_SERVICE
        sudo systemctl enable $MQTT_SERVICE
        if [ $? -eq 0 ]; then
            echo "✅ MQTT服务启动成功"
        else
            echo "❌ MQTT服务启动失败"
            exit 1
        fi
        ;;
    stop)
        echo "停止MQTT服务..."
        sudo systemctl stop $MQTT_SERVICE
        if [ $? -eq 0 ]; then
            echo "✅ MQTT服务已停止"
        else
            echo "❌ MQTT服务停止失败"
            exit 1
        fi
        ;;
    restart)
        echo "重启MQTT服务..."
        sudo systemctl restart $MQTT_SERVICE
        if [ $? -eq 0 ]; then
            echo "✅ MQTT服务重启成功"
        else
            echo "❌ MQTT服务重启失败"
            exit 1
        fi
        ;;
    status)
        echo "检查MQTT服务状态..."
        if netstat -tuln | grep -q ":$MQTT_PORT "; then
            echo "✅ MQTT服务正在运行（端口$MQTT_PORT）"
            sudo systemctl status $MQTT_SERVICE --no-pager -l
        else
            echo "❌ MQTT服务未运行（端口$MQTT_PORT）"
            sudo systemctl status $MQTT_SERVICE --no-pager -l
        fi
        ;;
    install)
        echo "安装MQTT服务..."
        sudo apt update
        sudo apt install -y mosquitto mosquitto-clients
        if [ $? -eq 0 ]; then
            echo "✅ MQTT服务安装成功"
            echo "启动MQTT服务..."
            sudo systemctl start mosquitto
            sudo systemctl enable mosquitto
            echo "✅ MQTT服务已启动并设置为开机自启"
        else
            echo "❌ MQTT服务安装失败"
            exit 1
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|install}"
        echo ""
        echo "命令说明："
        echo "  start   - 启动MQTT服务"
        echo "  stop    - 停止MQTT服务"
        echo "  restart - 重启MQTT服务"
        echo "  status  - 查看MQTT服务状态"
        echo "  install - 安装MQTT服务"
        echo ""
        echo "示例："
        echo "  $0 status    # 检查MQTT状态"
        echo "  $0 start     # 启动MQTT服务"
        echo "  $0 install   # 安装MQTT服务"
        exit 1
        ;;
esac 