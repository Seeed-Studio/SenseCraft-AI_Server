# SenseCraft AI Server 文档

本目录包含SenseCraft AI Server的所有文档。

## 核心文档

### 快速开始
- [run-with-docker.md](run-with-docker.md) - Docker部署指南（推荐）
- [run-in-host.md](run-in-host.md) - 主机部署指南
- [web-ui.md](web-ui.md) - Web界面使用说明

### 功能文档
- [mqtt-output.md](mqtt-output.md) - MQTT输出配置
- [mjpeg.md](mjpeg.md) - MJPEG流媒体说明
- [UPLOAD_FEATURES.md](UPLOAD_FEATURES.md) - 文件上传功能说明

### 技术文档
- [design.md](design.md) - 系统设计文档
- [README_LOGGING.md](README_LOGGING.md) - 日志系统说明
- [MQTT_FIX_README.md](MQTT_FIX_README.md) - MQTT修复说明

### 使用示例
- [example_usage.md](example_usage.md) - 使用示例和最佳实践

## 文档结构

```
docs/
├── README.md                    # 本文档
├── run-with-docker.md          # Docker部署
├── run-in-host.md              # 主机部署
├── web-ui.md                   # Web界面
├── mqtt-output.md              # MQTT配置
├── mjpeg.md                    # 流媒体
├── UPLOAD_FEATURES.md          # 文件上传
├── design.md                   # 系统设计
├── README_LOGGING.md           # 日志系统
├── MQTT_FIX_README.md          # MQTT修复
└── example_usage.md            # 使用示例
```

## 快速导航

### 新用户
1. 运行 `./scripts/test-run.sh` 检查环境
2. 查看 [run-with-docker.md](run-with-docker.md) 快速部署
3. 启动后访问 `http://localhost:46654/` 使用Web界面
4. 参考 [example_usage.md](example_usage.md) 学习最佳实践

### 开发者
1. 阅读 [design.md](design.md) 了解系统架构
2. 查看 [UPLOAD_FEATURES.md](UPLOAD_FEATURES.md) 了解新功能
3. 参考 [README_LOGGING.md](README_LOGGING.md) 配置日志

### 运维人员
1. 查看 [run-in-host.md](run-in-host.md) 了解生产部署
2. 阅读 [mqtt-output.md](mqtt-output.md) 配置MQTT
3. 参考 [mjpeg.md](mjpeg.md) 优化流媒体性能 