# 脚本文件说明

本目录包含SenseCraft AI Server的所有管理脚本。

## 脚本列表

### 🚀 主要脚本

#### `run.sh` - 主启动脚本
**功能**: 启动SenseCraft AI Server
**特点**:
- 自动检查并构建Docker镜像（scas）
- 检测MQTT服务状态
- 启动AI推理服务
- 显示启动日志

**用法**:
```bash
bash scripts/run.sh
```

#### `dev.sh` - 开发模式脚本
**功能**: 以交互模式启动服务（用于开发调试）
**特点**:
- 交互式终端
- 实时日志输出
- 容器退出时自动清理

**用法**:
```bash
bash scripts/dev.sh
```

### 🔧 管理脚本

#### `mqtt.sh` - MQTT服务管理
**功能**: 管理MQTT消息代理服务
**命令**:
- `./scripts/mqtt.sh status` - 检查MQTT服务状态
- `./scripts/mqtt.sh start` - 启动MQTT服务
- `./scripts/mqtt.sh stop` - 停止MQTT服务
- `./scripts/mqtt.sh restart` - 重启MQTT服务
- `./scripts/mqtt.sh install` - 安装MQTT服务

**用法**:
```bash
# 检查MQTT状态
./scripts/mqtt.sh status

# 启动MQTT服务
./scripts/mqtt.sh start
```

#### `test-run.sh` - 环境检查脚本
**功能**: 检查运行环境（不启动服务）
**检查项目**:
- Docker镜像是否存在
- MQTT服务状态
- 容器状态
- 必要目录和文件
- Dockerfile存在性

**用法**:
```bash
./scripts/test-run.sh
```

## 使用流程

### 首次使用
1. **环境检查**: `./scripts/test-run.sh`
2. **启动MQTT**: `./scripts/mqtt.sh start`（如果需要）
3. **启动服务**: `bash scripts/run.sh`
4. **访问界面**: `http://localhost:46654/`

### 日常使用
1. **启动服务**: `bash scripts/run.sh`
2. **访问界面**: `http://localhost:46654/`

### 开发调试
1. **开发模式**: `bash scripts/dev.sh`
2. **实时调试**: 在交互式终端中查看日志

## 脚本权限

确保脚本有执行权限：
```bash
chmod +x scripts/*.sh
```

## 故障排除

### 常见问题

1. **权限不足**
   ```bash
   sudo chmod +x scripts/*.sh
   ```

2. **MQTT服务未启动**
   ```bash
   ./scripts/mqtt.sh start
   ```

3. **Docker镜像不存在**
   ```bash
   # run.sh会自动构建，或手动构建：
   docker build -t scas .
   ```

4. **端口被占用**
   ```bash
   # 检查端口使用情况
   netstat -tuln | grep 46654
   netstat -tuln | grep 1883
   ```

### 日志查看

```bash
# 查看容器日志
sudo docker logs edge-gateway-container -f

# 查看MQTT服务日志
sudo journalctl -u mosquitto -f
```

## 脚本开发

如需修改脚本，请注意：
- 保持脚本的可移植性
- 添加适当的错误处理
- 提供清晰的输出信息
- 遵循bash最佳实践

---

**提示**: 首次使用建议先运行 `./scripts/test-run.sh` 检查环境！ 