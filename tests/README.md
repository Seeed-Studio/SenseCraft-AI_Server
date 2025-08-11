# 测试文件目录

本目录包含SenseCraft AI Server的各种测试和演示文件。

## 文件说明

### MQTT相关测试
- `test_mqtt.py` - MQTT连接和消息发布测试
- `test_mqtt_fix.py` - MQTT修复后的测试脚本
- `start_mqtt_test.sh` - MQTT测试启动脚本

### 前端功能演示
- 所有前端功能已集成到主界面 `http://localhost:46654/`
- 包括文件上传、模型管理、折叠界面等功能

## 使用方法

### MQTT测试
```bash
# 启动MQTT测试
./start_mqtt_test.sh

# 或者直接运行Python测试
python test_mqtt.py
python test_mqtt_fix.py
```

### 前端演示
1. 启动服务器：`bash scripts/run.sh`
2. 访问主界面：`http://localhost:46654/`
3. 测试各种功能：文件上传、模型管理、视频流等

## 注意事项
- 运行测试前请确保相关服务已启动
- 所有功能已集成到主界面，无需单独测试文件
- 生产环境直接使用 `http://localhost:46654/` 即可 