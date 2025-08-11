# SenseCraft AI Server - 日志功能增强

## 🎯 修复和新增功能

### 1. NaN值错误修复
- **问题**: 在绘制检测框时遇到NaN值导致 `ValueError: cannot convert float NaN to integer` 错误
- **解决方案**: 添加了 `safe_plot()` 函数来安全处理包含NaN值的检测结果
- **位置**: `src/streamer.py`

### 2. 详细启动日志
- **新增**: 服务器启动时显示详细的配置信息
- **包含**: 服务器地址、端口、模型路径、源文件路径等
- **位置**: `src/main.py`

### 3. 连接日志
- **新增**: 客户端连接时的详细日志
- **包含**: 客户端IP、请求路径、流媒体参数等
- **位置**: `src/streamer.py`

### 4. 移除云端同步逻辑
- **移除**: 所有云端模型同步和下载功能
- **简化**: 模型管理改为纯本地目录管理
- **位置**: `src/file_manager.py`, `src/constant.py`, `src/env_helper.py`

### 5. 新增模型列表API
- **新增**: `/models/list` 接口，提供可用模型列表
- **功能**: 自动扫描models目录，返回模型信息
- **位置**: `src/streamer.py`, `src/file_manager.py`

## 🚀 启动服务器

### 方法1: 使用启动脚本（推荐）
```bash
./start_server.sh
```

### 方法2: 直接运行
```bash
python3 src/main.py
```

### 方法3: 使用Docker
```bash
bash scripts/run.sh
```

## 📋 启动日志示例

服务器启动时会显示类似以下信息：

```
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 15, => === SenseCraft AI Server 启动中 ===
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 16, => 日志系统初始化完成...
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 25, => HTTP服务器模式启动中...
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 40, => ============================================================
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 41, => 🎉 SenseCraft AI Server 启动成功!
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 42, => 📡 服务器地址: http://192.168.1.100:46654
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 43, => 🔧 端口: 46654
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 44, => 📁 模型路径: /opt/dev/models
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 45, => 📁 源文件路径: /opt/dev/sources
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 46, => 📁 配置文件路径: /opt/dev/configs
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 47, => 🌐 版本: v0.0.1
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 48, => ============================================================
[YOLOv8-MJPEG]2024-01-01 12:00:00[INFO] src/main.py, line 49, => 🚀 服务器正在运行，等待连接...
```

## 🔗 连接日志示例

当客户端连接时会显示：

```
[YOLOv8-MJPEG]2024-01-01 12:01:00[INFO] src/streamer.py, line 225, => 🔗 客户端连接: 192.168.1.50 - 请求路径: /stream
[YOLOv8-MJPEG]2024-01-01 12:01:00[INFO] src/streamer.py, line 295, => 🎬 开始流媒体传输 - 客户端: 192.168.1.50 - 模型: 80-object-detect - 源: /opt/dev/sources/sample.mp4
```

## 🧪 测试服务器

使用提供的测试脚本验证服务器是否正常运行：

```bash
python3 test_server.py
```

或者指定特定的主机和端口：

```bash
python3 test_server.py 192.168.1.100 46654
```

## 🤖 模型管理

### 支持的模型格式
- **TensorRT**: `.engine` 文件
- **PyTorch**: `.pt` 文件
- **ONNX**: `.onnx` 文件

### 模型列表API
```bash
# 获取可用模型列表
curl http://localhost:46654/models/list

# 响应示例
{
  "list": [
    {
      "downloadUrl": "",
      "name": "yolov8n (PyTorch)",
      "size": 1234567,
      "icon": "",
      "arguments": {
        "uuid": "yolov8n",
        "type": "PyTorch",
        "task": "detect",
        "half": false
      },
      "file_path": "/path/to/models/yolov8n.pt",
      "filename": "yolov8n.pt"
    }
  ],
  "page": 1,
  "size": 1
}
```

### 重新加载模型
```bash
# 重新扫描模型目录
curl -X POST http://localhost:46654/reloadModels
```

## 🔧 环境变量配置

可以通过环境变量自定义配置：

```bash
export EDGEAI_LOG_LEVEL="20"        # 日志级别 (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR)
export EDGEAI_MQTT_STARTUP="OFF"    # MQTT开关 (ON/OFF)
export EDGEAI_PORT="46654"          # 服务器端口
export EDGEAI_IP=""                 # 服务器IP (空表示所有接口)
```

## 📝 日志级别说明

- **DEBUG (10)**: 详细的调试信息
- **INFO (20)**: 一般信息（默认）
- **WARNING (30)**: 警告信息
- **ERROR (40)**: 错误信息
- **CRITICAL (50)**: 严重错误

## 🐛 故障排除

### 1. NaN值错误
如果仍然遇到NaN值错误，日志会显示：
```
[WARNING] 检测到NaN值，禁用检测框显示: cannot convert float NaN to integer
```

### 2. 连接问题
检查防火墙设置和端口是否被占用：
```bash
netstat -tlnp | grep 46654
```

### 3. 权限问题
确保脚本有执行权限：
```bash
chmod +x start_server.sh
```

## 📞 支持

如果遇到问题，请检查：
1. 日志输出中的错误信息
2. 网络连接状态
3. 文件权限设置
4. 依赖包是否正确安装 