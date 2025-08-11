# MQTT回调API版本修复说明

## 🐛 问题描述

在使用较新版本的paho-mqtt库（1.6.1）时，出现了以下警告和错误：

1. **回调API版本警告**：
   ```
   Unsupported callback API version: version 2.0 added a callback_api_version, see docs/migrations.rst for details
   ```

2. **AttributeError错误**：
   ```
   Exception ignored in: <function Client.__del__ at 0xfffeee2ef7f0>
   AttributeError: 'Client' object has no attribute '_sock'
   ```

## 🔧 修复内容

### 1. 回调API版本兼容性修复

**文件**: `src/mqtt_driver.py`

**修改**: 在创建MQTT客户端时添加`callback_api_version`参数

```python
# 修改前
self.client = mqtt_client.Client(self.client_id)

# 修改后  
self.client = mqtt_client.Client(self.client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1)
```

### 2. 连接状态管理

**文件**: `src/mqtt_driver.py`

**新增功能**:
- 添加`_connected`状态标志
- 改进连接错误处理
- 在发布消息前检查连接状态

### 3. 安全清理机制

**文件**: `src/mqtt_driver.py` 和 `src/mqtt_handler.py`

**新增功能**:
- 添加`cleanup()`方法安全清理MQTT连接
- 添加`__del__()`析构函数防止AttributeError
- 改进错误处理和异常捕获

## 📋 修复详情

### MqttDriver类改进

1. **连接状态跟踪**: 添加`_connected`标志跟踪连接状态
2. **异常处理**: 连接失败时不会抛出异常，而是记录警告
3. **安全清理**: 添加清理方法防止资源泄漏
4. **发布检查**: 发布消息前检查连接状态

### MqttHandler类改进

1. **错误处理**: 改进消息处理和服务器启动的错误处理
2. **资源清理**: 添加析构函数确保资源正确清理
3. **优雅关闭**: 支持KeyboardInterrupt信号处理

## ✅ 修复效果

修复后应该不再出现：
- ✅ 回调API版本警告
- ✅ AttributeError异常
- ✅ 连接相关的崩溃

## 🚀 使用方法

修复后，您可以正常使用原有的启动方式：

```bash
# 使用Docker启动
bash scripts/dev.sh

# 或直接运行
python3 src/main.py
```

## 📝 注意事项

1. 修复保持了向后兼容性，不会影响现有功能
2. 连接失败时会记录警告但不会阻止程序运行
3. 资源清理更加安全，防止内存泄漏
4. 支持优雅关闭，按Ctrl+C可以正常退出

## 🔍 验证修复

启动服务器后，应该看到正常的启动日志，不再出现回调API版本警告或AttributeError异常。 