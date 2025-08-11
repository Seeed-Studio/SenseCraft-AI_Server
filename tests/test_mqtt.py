#!/usr/bin/env python3
"""
MQTT数据接口测试脚本
"""

import requests
import json
import time

def test_mqtt_data():
    """测试MQTT数据接口"""
    base_url = "http://localhost:46654"
    
    print("🧪 测试MQTT数据接口")
    print("=" * 50)
    
    try:
        # 测试MQTT数据接口
        response = requests.get(f"{base_url}/mqtt/data", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ MQTT数据接口测试成功")
            print(f"📊 响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success'):
                mqtt_data = data.get('data', {})
                print(f"\n📈 检测结果:")
                print(f"   UUID: {mqtt_data.get('uuid', 'N/A')}")
                print(f"   总检测数: {mqtt_data.get('total_detections', 0)}")
                print(f"   FPS: {mqtt_data.get('fps', 0)}")
                print(f"   置信度: {mqtt_data.get('confidence', 0):.2%}")
                
                if mqtt_data.get('info'):
                    print(f"   检测对象:")
                    for obj, count in mqtt_data['info'].items():
                        print(f"     - {obj}: {count}")
            else:
                print("❌ 接口返回失败状态")
                
        else:
            print(f"❌ 接口请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_continuous_mqtt():
    """连续测试MQTT数据"""
    base_url = "http://localhost:46654"
    
    print("\n🔄 连续测试MQTT数据（5次）")
    print("=" * 50)
    
    for i in range(5):
        try:
            response = requests.get(f"{base_url}/mqtt/data", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    mqtt_data = data.get('data', {})
                    print(f"第{i+1}次: 检测到 {mqtt_data.get('total_detections', 0)} 个对象, "
                          f"FPS: {mqtt_data.get('fps', 0)}, "
                          f"置信度: {mqtt_data.get('confidence', 0):.2%}")
                else:
                    print(f"第{i+1}次: 接口返回失败")
            else:
                print(f"第{i+1}次: 请求失败 {response.status_code}")
        except Exception as e:
            print(f"第{i+1}次: 错误 {str(e)}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_mqtt_data()
    test_continuous_mqtt() 