# SenseCraft AI Server 中文版

[English](README.md) | [中文](README_CN.md)

SenseCraft AI Server 是一个基于边缘计算的AI推理服务器，支持实时视频流处理和对象检测。本项目提供了完整的Web界面，让用户可以轻松配置和管理AI推理任务。

## 🚀 快速开始

### 环境要求
- Docker（推荐）或 Python 3.8+
- NVIDIA Jetson 设备（支持TensorRT加速）
- 网络连接（用于下载模型）

### 一键启动
```sh
# 确保已安装Docker，然后运行
bash scripts/run.sh

# 脚本会自动：
# 1. 检查并构建Docker镜像（如果需要）
# 2. 检查MQTT服务状态
# 3. 启动SenseCraft AI Server

# 访问Web界面
# 本机访问
http://localhost:46654/
# 远程访问（替换为您的机器IP）
http://机器IP:46654/
```

### MQTT服务管理
```sh
# 检查MQTT服务状态
./scripts/mqtt.sh status

# 启动MQTT服务
./scripts/mqtt.sh start

# 安装MQTT服务（如果未安装）
./scripts/mqtt.sh install
```

### 环境检查
```sh
# 检查运行环境（不启动服务）
./scripts/test-run.sh

# 查看所有可用脚本
ls -la scripts/
```

## ✨ 主要功能

### 🎮 智能控制面板
- **视频源配置**：支持本地文件、USB摄像头、RTSP流
- **AI模型选择**：实时切换不同的AI模型
- **参数调优**：调整置信度、检测限制、显示选项
- **流控制**：开始、停止、暂停、恢复视频流

### 📁 文件管理
- **视频上传**：拖拽上传视频文件进行处理
- **模型上传**：添加各种格式的AI模型
- **文件管理**：查看、删除、组织上传的文件
- **折叠界面**：整洁、有序的布局，支持展开/折叠

### 📊 实时监控
- **实时视频流**：MJPEG流媒体，带AI叠加层
- **MQTT集成**：通过MQTT实时获取检测结果
- **状态指示器**：连接状态、FPS、检测计数
- **性能指标**：实时监控系统性能

### ⚙️ 高级功能
- **模型热切换**：无需重启即可更换模型
- **参数持久化**：设置自动保存和恢复
- **响应式设计**：支持桌面和移动设备
- **错误处理**：配置问题的清晰反馈

## 🛠️ 详细安装

### 使用Docker（推荐）

```sh
# 拉取预构建镜像
docker pull seeedcloud/edge-gateway:mis-1.0

# 启动服务
bash scripts/run.sh

# 访问界面
http://localhost:46654/
```

### 主机安装

```sh
# 安装依赖
pip install numba ultralytics "opencv-python-headless<4.3" numpy==1.23.5

# 安装MQTT代理（可选）
sudo apt update && sudo apt install mosquitto

# 安装项目依赖
pip install -r requirements.txt

# 启动服务
python3 src/main.py

# 访问界面
http://localhost:46654/
```

## 📖 使用指南

### 1. 启动服务器
```sh
bash scripts/run.sh
```

### 2. 打开浏览器
访问 `http://localhost:46654/`

### 3. 配置设置
- 选择视频源（文件、摄像头、RTSP）
- 选择AI模型
- 调整参数（置信度、检测限制等）

### 4. 开始推理
点击"开始推理"按钮

### 5. 监控结果
- 查看实时视频流
- 监控MQTT数据
- 观察检测结果

## 📁 项目结构

```
SenseCraft-AI_Server/
├── src/                    # Python源代码
│   ├── main.py            # 主程序入口
│   ├── camera.py          # 摄像头和视频处理
│   ├── output.py          # 输出流处理
│   ├── streamer.py        # MJPEG流和HTTP API
│   ├── file_manager.py    # 文件管理
│   └── mqtt_handler.py    # MQTT处理
├── dist/                   # Web界面文件
├── models/                 # AI模型目录
├── sources/                # 视频源目录
├── configs/                # 配置文件
├── scripts/                # 脚本文件
├── docs/                   # 文档目录
└── tests/                  # 测试文件
```

## 🔧 配置说明

### 环境变量
- `EDGEAI_PORT`: 服务端口（默认46654）
- `EDGEAI_LOG_LEVEL`: 日志级别
- `EDGEAI_MQTT_STARTUP`: MQTT启动开关
- `EDGEAI_ONLINE`: 在线模式开关

### 文件路径
- `EDGEAI_MODELS_PATH`: 模型文件路径
- `EDGEAI_SOURCES_PATH`: 视频源路径
- `EDGEAI_CONFIGS_PATH`: 配置文件路径
- `EDGEAI_WEB_DIST_PATH`: Web界面路径

## 📚 高级功能

### 文件上传
- 支持拖拽上传视频文件
- 支持上传AI模型文件
- 实时显示上传进度
- 文件类型自动识别

### 模型管理
- 支持多种模型格式
- 模型热切换功能
- 模型性能监控
- 自动模型验证

### MQTT集成
- 实时检测结果推送
- 可配置的MQTT主题
- 连接状态监控
- 数据格式自定义

## 🐛 故障排除

### 常见问题

1. **无法访问Web界面**
   - 检查端口46654是否被占用
   - 确认防火墙设置
   - 验证Docker容器状态

2. **视频流无法显示**
   - 检查视频文件格式
   - 确认摄像头权限
   - 验证RTSP流地址

3. **模型加载失败**
   - 检查模型文件完整性
   - 确认模型格式支持
   - 验证TensorRT兼容性

### 日志查看
```sh
# Docker容器日志
docker logs edge-ai-backend -f

# 主机运行日志
tail -f logs/edge-ai.log
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [项目主页](https://github.com/Seeed-Studio/SenseCraft-AI_Server)
- [Web界面源码](https://github.com/Seeed-Studio/SenseCraft-AI-webUI)
- [Docker镜像](https://hub.docker.com/r/seeedcloud/edge-gateway)
- [技术文档](docs/)

## 📞 支持

如果您遇到问题或有建议，请：
- 提交GitHub Issue
- 查看[文档目录](docs/)
- 参考[使用示例](docs/example_usage.md)

---

**开始使用SenseCraft AI Server，体验强大的边缘AI推理能力！** 🚀 