# IoT 多协议支持实现指南

## 概述

本项目现在支持多种IoT协议，实现统一的设备通信接口。当前实现的协议包括：

- ✅ **MQTT** - 轻量级消息传递协议（完全支持）
- ✅ **CoAP** - 受限应用协议（完全支持）
- ✅ **AMQP** - 高级消息队列协议（完全支持）

## 新增文件

### 核心协议架构

1. **`app/services/protocol_base.py`** - 协议抽象基类
   - 定义所有协议必须实现的接口
   - 提供数据标准化方法

2. **`app/services/protocol_registry.py`** - 协议注册器
   - 单例模式管理所有协议服务
   - 提供服务发现和路由功能

3. **`app/services/protocol_manager.py`** - 协议管理器
   - 统一管理协议生命周期
   - 简化协议初始化和关闭

### 协议实现

4. **`app/services/coap_service.py`** - CoAP协议服务
   - 支持GET、POST、PUT、DELETE方法
   - 轻量级，适合受限设备

5. **`app/services/amqp_service.py`** - AMQP协议服务
   - 企业级可靠消息传递
   - 支持交换机和路由键

6. **`app/services/device_command_service.py`** - 设备命令服务
   - 统一处理多协议设备命令
   - 自动记录命令历史

### 文档

7. **`docs/PROTOCOL_EXAMPLES.md`** - 协议使用示例
   - 详细的代码示例
   - 最佳实践指南

8. **`PROTOCOL_GUIDE.md`** - 本文档

## 快速开始

### 1. 安装协议依赖

```bash
# 安装CoAP支持
pip install aiocoap

# 安装AMQP支持
pip install pika

# 安装蓝牙支持
pip install bleak

# 或者安装所有可选依赖
pip install -r requirements.txt
```

### 2. 启动应用

应用启动时会自动：
- 注册所有可用的协议服务
- 启动协议管理器
- 初始化协议连接

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 检查协议状态

```bash
curl http://localhost:8000/health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "protocols": {
    "mqtt": {
      "connected": true,
      "device_count": 5
    },
    "coap": {
      "connected": true,
      "device_count": 3
    },
    "amqp": {
      "connected": false,
      "device_count": 0
    }
  },
  "all_protocols_connected": false
}
```

## 使用示例

### 发送命令到MQTT设备

```python
from app.services.device_command_service import device_command_service

command_id = await device_command_service.send_command(
    device_id=1,
    command_type="control",
    command_data={
        "device_id": "sensor_001",
        "data": {"action": "reset"}
    }
)
```

### 发送命令到CoAP设备

```python
from app.services.protocol_registry import protocol_registry

device_config = {
    "device_id": "coap_sensor_001",
    "protocol": "coap",
    "endpoint": "coap://device.local:5683",
    "resources": {
        "control": "/actuator/control"
    }
}

await protocol_registry.send_command_to_device(
    device_config,
    {
        "resource": "/actuator/control",
        "method": "POST",
        "payload": {"action": "turn_on"},
        "content_format": "application/json"
    }
)
```

### 发送命令到AMQP设备

```python
from app.services.protocol_registry import protocol_registry

device_config = {
    "device_id": "amqp_device_001",
    "protocol": "amqp",
    "host": "rabbitmq.example.com",
    "exchange": "iot_devices",
    "routing_key": "device.amqp_device_001"
}

await protocol_registry.send_command_to_device(
    device_config,
    {
        "routing_key": "device.amqp_device_001.command",
        "payload": {"command": "update_config"},
        "properties": {"message_id": "cmd_001"}
    }
)
```

## 添加新协议

要添加新协议（如蓝牙、Zigbee等），请遵循以下步骤：

1. **创建协议服务类**
   ```python
   from app.services.protocol_base import ProtocolService

   class BluetoothService(ProtocolService):
       def __init__(self):
           super().__init__("bluetooth")
           # 初始化蓝牙逻辑

       async def connect_device(self, device_id, device_config):
           # 实现设备连接
           pass

       async def send_command(self, device_id, command):
           # 实现命令发送
           pass

       # 实现其他抽象方法...
   ```

2. **注册协议服务**
   ```python
   from app.services.bluetooth_service import bluetooth_service
   from app.services.protocol_registry import protocol_registry

   protocol_registry.register("bluetooth", bluetooth_service)
   ```

3. **在协议管理器中注册**
   ```python
   # 在 protocol_manager.py 的 _register_services() 方法中添加
   protocol_registry.register("bluetooth", bluetooth_service)
   ```

4. **更新设备配置**
   ```json
   {
     "device_id": "ble_device_001",
     "protocol": "bluetooth",
     "mac_address": "XX:XX:XX:XX:XX:XX",
     "services": [...]
   }
   ```

## 架构特点

### 1. 统一接口
所有协议都实现 `ProtocolService` 抽象基类，提供一致的API。

### 2. 协议注册器
使用单例模式的注册器管理所有协议服务，支持服务发现和路由。

### 3. 数据标准化
所有协议数据都标准化为统一格式：
```json
{
  "device_id": "device_123",
  "protocol": "mqtt",
  "timestamp": "2024-01-01T00:00:00Z",
  "data_type": "telemetry",
  "data": {...},
  "quality": "good"
}
```

### 4. 错误处理
每个协议服务都有完善的错误处理和日志记录。

### 5. 生命周期管理
协议管理器统一管理所有协议服务的启动和关闭。

## 性能考虑

1. **连接池**: 每个协议服务维护设备连接池
2. **异步操作**: 所有协议操作都使用异步模式
3. **资源管理**: 设备断开时自动清理资源
4. **监控**: 实时监控协议连接状态

## 安全考虑

1. **认证**: 支持协议级认证（用户名/密码、PSK等）
2. **加密**: 建议使用加密传输（TLS/SSL）
3. **访问控制**: 通过路由器和交换机实现访问控制
4. **数据验证**: 所有输入数据都经过验证

## 故障排除

### 协议服务未启动

检查依赖库是否安装：
```bash
pip list | grep aiocoap  # CoAP
pip list | grep pika     # AMQP
pip list | grep bleak    # Bluetooth
```

### 设备连接失败

检查设备配置是否包含必要的字段（protocol、endpoint等）。

### 命令发送失败

检查协议服务是否已连接，使用 `/health` 端点查看状态。

## 下一步计划

- [ ] 添加蓝牙（BLE）协议支持
- [ ] 添加Zigbee协议支持
- [ ] 添加LoRaWAN协议支持
- [ ] 添加Matter/Thread协议支持
- [ ] 实现协议间消息路由
- [ ] 添加协议性能监控

## 参考资料

- [CoAP 规范 (RFC 7252)](https://tools.ietf.org/html/rfc7252)
- [AMQP 0.9.1 规范](https://www.rabbitmq.com/resources/specs/amqp0-9-1-reference.pdf)
- [MQTT 协议文档](https://mqtt.org/documentation/)
- [AIoCoap 文档](https://aiocoap.readthedocs.io/)
- [Pika (AMQP) 文档](https://pika.readthedocs.io/)
- [BLEAK (Bluetooth) 文档](https://bleak.readthedocs.io/)

## 支持

如有问题或建议，请：
1. 查阅 `docs/PROTOCOL_EXAMPLES.md` 获取详细示例
2. 检查应用日志获取错误信息
3. 提交 Issue 或 Pull Request
