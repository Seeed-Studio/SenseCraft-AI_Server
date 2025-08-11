#!/usr/bin/env python3
"""
测试MQTT回调API修复
"""

import sys
import os
sys.path.insert(0, "src")

def test_mqtt_handler_creation():
    """测试MqttHandler创建是否正常"""
    try:
        from mqtt_handler import MqttHandler
        
        print("🧪 测试MqttHandler创建...")
        
        # 测试创建MqttHandler实例
        options = {
            "ip": "127.0.0.1",
            "port": 1883,
            "username": "test",
            "password": "test"
        }
        
        handler = MqttHandler(options)
        print("✅ MqttHandler创建成功")
        
        # 测试on_connect方法签名
        import inspect
        sig = inspect.signature(handler.on_connect)
        params = list(sig.parameters.keys())
        
        print(f"📋 on_connect方法参数: {params}")
        
        # 检查参数数量是否正确（应该是6个：self + 5个回调参数）
        if len(params) == 6:
            print("✅ on_connect方法参数数量正确")
        else:
            print(f"❌ on_connect方法参数数量错误，期望6个，实际{len(params)}个")
            return False
            
        # 检查参数名称是否正确
        expected_params = ['self', 'client', 'userdata', 'flags', 'reason_code', 'properties']
        if params == expected_params:
            print("✅ on_connect方法参数名称正确")
        else:
            print(f"❌ on_connect方法参数名称错误")
            print(f"期望: {expected_params}")
            print(f"实际: {params}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mqtt_driver_compatibility():
    """测试MqttDriver兼容性"""
    try:
        from mqtt_driver import MqttDriver
        
        print("\n🧪 测试MqttDriver兼容性...")
        
        # 测试创建MqttDriver实例
        driver = MqttDriver("127.0.0.1", 1883, "test", "test")
        print("✅ MqttDriver创建成功")
        
        # 检查回调API版本
        if hasattr(driver.client, 'callback_api_version'):
            print(f"✅ 使用回调API版本: {driver.client.callback_api_version}")
        else:
            print("⚠️  无法获取回调API版本信息")
            
        return True
        
    except Exception as e:
        print(f"❌ MqttDriver测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🔧 MQTT回调API修复验证")
    print("=" * 50)
    
    success = True
    
    # 测试MqttHandler
    if not test_mqtt_handler_creation():
        success = False
    
    # 测试MqttDriver
    if not test_mqtt_driver_compatibility():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！MQTT回调API修复成功")
    else:
        print("❌ 部分测试失败，请检查修复")
    
    print("\n💡 修复说明:")
    print("- 将on_connect方法的参数从5个增加到6个")
    print("- 添加了properties参数以支持MQTT V2回调API")
    print("- 将rc参数重命名为reason_code以保持一致性") 