# SenseCraft AI Server 使用示例

## 🚀 快速开始

### 1. 启动服务器
```bash
./start_server.sh
```

### 2. 准备模型文件
将您的AI模型文件放入 `models/` 目录：

```bash
# 示例：添加YOLOv8模型
cp yolov8n.pt models/
cp yolov8s.pt models/
cp object-detection.engine models/
```

### 3. 查看可用模型
```bash
curl http://localhost:46654/models/list
```

### 4. 开始流媒体推理
```bash
# 使用默认模型
curl http://localhost:46654/stream?src=sample.mp4

# 使用特定模型
curl http://localhost:46654/stream?model_id=yolov8n&src=sample.mp4

# 使用特定模型和参数
curl http://localhost:46654/stream?model_id=yolov8n&src=sample.mp4&conf=0.5&show_box=1&show_fps=1
```

## 📋 API接口

### 模型管理
- `GET /models/list` - 获取可用模型列表
- `POST /reloadModels` - 重新加载模型列表

### 源文件管理
- `GET /sources/list` - 获取源文件列表
- `POST /upload` - 上传源文件
- `GET /sources/del?name=filename` - 删除源文件

### 系统信息
- `GET /about` - 获取系统信息
- `GET /camList` - 获取可用摄像头列表
- `GET /appConfigs` - 获取应用配置

### 流媒体
- `GET /stream` - 开始流媒体推理

## 🔧 流媒体参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `model_id` | string | "80-object-detect" | 模型ID |
| `src` | string | "sample.mp4" | 源文件路径 |
| `fps` | int | 30 | 帧率 |
| `quality` | int | 50 | JPEG质量 |
| `conf` | float | 0.25 | 置信度阈值 |
| `max_det` | int | 300 | 最大检测数量 |
| `show_box` | int | 1 | 显示检测框 |
| `show_fps` | int | 0 | 显示FPS |
| `show_time` | int | 0 | 显示时间戳 |
| `track` | int | 0 | 启用目标跟踪 |
| `half` | int | 0 | 半精度推理 |

## 📁 目录结构

```
SenseCraft-AI_Server/
├── models/           # AI模型文件
│   ├── yolov8n.pt
│   ├── yolov8s.pt
│   └── object-detection.engine
├── sources/          # 源文件
│   ├── sample.mp4
│   └── test.jpg
├── configs/          # 配置文件
│   └── application.json
├── dist/             # 静态文件
└── src/              # 源代码
```

## 🐛 故障排除

### 1. 模型未找到
```
错误: AI model not found.
解决: 确保模型文件在 models/ 目录中，并调用 /reloadModels 接口
```

### 2. 源文件未找到
```
错误: Image Source not found.
解决: 确保 sources/sample.mp4 文件存在
```

### 3. 端口被占用
```bash
# 检查端口占用
netstat -tlnp | grep 46654

# 修改端口
export EDGEAI_PORT="8080"
```

## 📊 性能优化

### 1. 模型选择
- 使用TensorRT模型获得最佳性能
- 根据硬件选择合适的模型大小

### 2. 参数调优
- 调整 `conf` 参数平衡精度和速度
- 使用 `half=1` 启用半精度推理
- 调整 `max_det` 限制检测数量

### 3. 硬件加速
- 确保CUDA环境正确配置
- 使用支持TensorRT的GPU 