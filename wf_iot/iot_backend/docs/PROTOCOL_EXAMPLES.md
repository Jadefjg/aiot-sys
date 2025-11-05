# IoT 协议使用示例

本文档展示如何使用多协议IoT系统进行设备通信。

## 目录
- [设备配置](#设备配置)
- [发送命令](#发送命令)
- [接收数据](#接收数据)
- [跨协议通信](#跨协议通信)

## 设备配置

### MQTT 设备配置

```json
{
  "device_id": "sensor_001",
  "device_name": "温度传感器",
  "protocol": "mqtt",
  "endpoint": "mqtt://broker.example.com:1883",
  "topics": {
    "data": "device/sensor_001/data",
    "status": "device/sensor_001/status",
    "command": "device/sensor_001/command"
  },
  "credentials": {
    "username": "device_user",
    "password": "encrypted_password"
  },
  "options": {
    "qos": 1,
    "retain": false
  }
}
```

### CoAP 设备配置

```json
{
  "device_id": "coap_sensor_001",
  "device_name": "CoAP传感器",
  "protocol": "coap",
  "endpoint": "coap://device.local:5683",
  "resources": {
    "data": "/sensor/data",
    "status": "/device/status",
    "control": "/actuator/control",
    "heartbeat": "/.well-known/core"
  },
  "credentials": {
    "auth_method": "psk",
    "key": "device_secret_key"
  }
}
```

### AMQP 设备配置

```json
{
  "device_id": "amqp_device_001",
  "device_name": "AMQP工业设备",
  "protocol": "amqp",
  "host": "rabbitmq.example.com",
  "port": 5672,
  "exchange": "iot_devices",
  "routing_key": "device.amqp_device_001",
  "credentials": {
    "username": "device_user",
    "password": "device_password"
  },
  "queue_options": {
    "durable": true,
    "exclusive": false
  }
}
```

## 发送命令

### 使用设备命令服务

```python
from app.services.device_command_service import device_command_service

# 发送控制命令
command_id = await device_command_service.send_command(
    device_id=1,
    command_type="control",
    command_data={
        "device_id": "sensor_001",
        "data": {
            "action": "start",
            "parameter": "value"
        }
    },
    created_by=1
)

if command_id:
    print(f"Command sent successfully: {command_id}")
else:
    print("Command failed")
```

### 直接使用协议服务

```python
from app.services.protocol_registry import protocol_registry

# 发送MQTT命令
mqtt_device = {
    "device_id": "sensor_001",
    "protocol": "mqtt",
    "endpoint": "mqtt://broker.example.com:1883"
}

await protocol_registry.send_command_to_device(
    mqtt_device,
    {
        "topic": "device/sensor_001/command",
        "payload": {
            "action": "reset",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "qos": 1
    }
)

# 发送CoAP命令
coap_device = {
    "device_id": "coap_sensor_001",
    "protocol": "coap",
    "endpoint": "coap://device.local:5683"
}

await protocol_registry.send_command_to_device(
    coap_device,
    {
        "resource": "/actuator/control",
        "method": "POST",
        "payload": {"action": "turn_on"},
        "content_format": "application/json"
    }
)

# 发送AMQP命令
amqp_device = {
    "device_id": "amqp_device_001",
    "protocol": "amqp",
    "host": "rabbitmq.example.com",
    "exchange": "iot_devices",
    "routing_key": "device.amqp_device_001"
}

await protocol_registry.send_command_to_device(
    amqp_device,
    {
        "routing_key": "device.amqp_device_001.command",
        "payload": {
            "command": "update_config",
            "parameters": {"setting": "value"}
        },
        "properties": {
            "message_id": "cmd_001",
            "reply_to": "device.response"
        }
    }
)
```

## 接收数据

### 处理设备数据

```python
from app.services.protocol_registry import protocol_registry
from app.db.session import SessionLocal
from app.crud.device import device_crud

# 模拟接收MQTT数据
mqtt_data = {
    "type": "telemetry",
    "temperature": 25.5,
    "humidity": 60,
    "timestamp": "2024-01-01T00:00:00Z"
}

normalized_data = await protocol_registry.handle_device_message(
    protocol="mqtt",
    device_id="sensor_001",
    data=mqtt_data
)

# 存储到数据库
db = SessionLocal()
try:
    if normalized_data:
        # 使用device_crud.record_device_data存储数据
        device_crud.record_device_data(db, normalized_data)
        print(f"Data stored: {normalized_data}")
finally:
    db.close()
```

### 自定义数据处理器

```python
class CustomDataHandler:
    """自定义数据处理器示例"""

    async def handle_sensor_data(self, data: dict):
        """处理传感器数据"""
        if data.get("temperature") > 30:
            # 发送高温警报
            await self.send_alert(data["device_id"], "HIGH_TEMPERATURE")

        if data.get("humidity") < 20:
            # 发送低湿度警报
            await self.send_alert(data["device_id"], "LOW_HUMIDITY")

    async def send_alert(self, device_id: str, alert_type: str):
        """发送警报"""
        # 实现警报逻辑
        print(f"Alert: {alert_type} for device {device_id}")
```

## 跨协议通信

### 协议转换示例

```python
async def translate_mqtt_to_coap(mqtt_command: dict, coap_device_config: dict):
    """将MQTT命令转换为CoAP格式"""

    # 解析MQTT命令
    action = mqtt_command["payload"]["action"]

    # 转换为CoAP格式
    coap_command = {
        "resource": "/actuator/control",
        "method": "POST",
        "payload": {
            "original_command": action,
            "translated_from": "mqtt",
            "device_id": coap_device_config["device_id"]
        },
        "content_format": "application/json"
    }

    # 发送CoAP命令
    success = await protocol_registry.send_command_to_device(
        coap_device_config,
        coap_command
    )

    return success
```

### 聚合多协议数据

```python
async def aggregate_device_data(device_configs: list):
    """聚合来自多个协议设备的传感器数据"""

    data_aggregator = {
        "temperature": [],
        "humidity": [],
        "timestamp": datetime.now().isoformat()
    }

    for device_config in device_configs:
        protocol = device_config.get("protocol")
        device_id = device_config.get("device_id")

        # 获取最新数据
        service = protocol_registry.get_service(protocol)
        if service:
            device_status = service.get_device_status(device_id)
            if device_status and "last_data" in device_status:
                data = device_status["last_data"]

                # 聚合数据
                if "temperature" in data:
                    data_aggregator["temperature"].append(data["temperature"])
                if "humidity" in data:
                    data_aggregator["humidity"].append(data["humidity"])

    # 计算平均值
    if data_aggregator["temperature"]:
        data_aggregator["avg_temperature"] = sum(data_aggregator["temperature"]) / len(data_aggregator["temperature"])

    if data_aggregator["humidity"]:
        data_aggregator["avg_humidity"] = sum(data_aggregator["humidity"]) / len(data_aggregator["humidity"])

    return data_aggregator
```

## 协议管理器使用

```python
from app.services.protocol_manager import protocol_manager

# 初始化协议管理器
protocol_manager.initialize()

# 检查协议支持
if protocol_manager.is_protocol_supported("mqtt"):
    print("MQTT is supported")

# 获取支持的协议列表
protocols = protocol_manager.get_supported_protocols()
print(f"Supported protocols: {protocols}")

# 获取服务状态
statuses = protocol_manager.get_service_status()
for status in statuses:
    print(f"{status['protocol']}: {status['connected']} ({status['device_count']} devices)")

# 重启特定协议
await protocol_manager.restart_protocol("mqtt")

# 连接设备
await protocol_manager.connect_device(
    "device_001",
    {"protocol": "mqtt", "endpoint": "mqtt://broker.example.com:1883"}
)

# 发送命令
await protocol_manager.send_command(
    {"protocol": "mqtt", "device_id": "device_001"},
    {"action": "reset"}
)
```

## 错误处理

```python
try:
    result = await protocol_registry.send_command_to_device(
        device_metadata,
        command_data
    )
    if not result:
        logger.warning(f"Command failed for device {device_metadata['device_id']}")
except ValueError as e:
    # 协议不支持
    logger.error(f"Protocol error: {e}")
except Exception as e:
    # 其他错误
    logger.error(f"Unexpected error: {e}")
```

## 最佳实践

1. **始终检查协议支持**: 在发送命令前使用 `is_protocol_supported()` 检查
2. **使用设备命令服务**: 统一使用 `DeviceCommandService` 可以自动记录命令历史
3. **处理异常**: 所有协议操作都可能失败，必须捕获和处理异常
4. **资源清理**: 断开设备连接时使用 `disconnect_device()`
5. **监控连接状态**: 定期检查协议服务的连接状态
6. **标准化数据**: 所有协议数据都应标准化为JSON格式存储
7. **日志记录**: 使用 `logger` 记录关键操作和错误

## 故障排除

### 协议服务未启动

```python
# 检查服务状态
statuses = protocol_manager.get_service_status()
for status in statuses:
    if not status["connected"]:
        logger.error(f"{status['protocol']} service is not connected")

# 重启失败的服务
await protocol_manager.restart_protocol("mqtt")
```

### 设备连接失败

```python
# 检查设备配置
device_config = device.device_metadata
if not device_config.get("protocol"):
    logger.error(f"Device {device.device_id} has no protocol configured")

# 检查协议服务是否可用
if not protocol_manager.is_protocol_supported(device_config["protocol"]):
    logger.error(f"Protocol {device_config['protocol']} is not supported")

# 重新连接
await protocol_manager.disconnect_device(device.device_id, device_config["protocol"])
await asyncio.sleep(1)
success = await protocol_manager.connect_device(
    device.device_id,
    device_config
)
```

### 命令发送失败

```python
# 检查设备是否在线
service = protocol_registry.get_service(device_config["protocol"])
device_status = service.get_device_status(device_id)

if not device_status or device_status["status"] != "online":
    logger.error(f"Device {device_id} is not online")

# 检查命令格式
if not command_data.get("action"):
    logger.error("Command missing 'action' field")
    return False
```
