import json
import logging
import paho.mqtt.client as mqtt

from typing import Optional
from datetime import datetime

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_crud, device_data_crud, device_command_crud
from app.schemas.device import DeviceDataCreate, DeviceUpdate

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")

            # 订阅设备相关主题
            topics = [
                "device/+/data",  # 设备数据上报
                "device/+/status",  # 设备状态上报
                "device/+/command/response",  # 命令响应
                "device/+/heartbeat",  # 设备心跳
                "device/+/firmware/status"  # 固件升级状态
            ]
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            self.connected = False
            logger.error("Failed to connect to MQTT broker, return code{rc}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, return code{rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.info(f"Received message on topic: {topic} -> payload: {payload}")

            # 解析主题
            topic_parts = topic.split("/")
            if len(topic_parts) < 3:
                logger.warning(f"Invalid topic format:{topic}")
                return
            device_id = topic_parts[1]
            message_type = topic_parts[2]

            # 处理不同类型的消息
            if message_type == "data":
                self._handle_device_data(device_id,payload)
            elif message_type == "status":
                self._handle_device_status(device_id,payload)
            elif message_type == "heartbeat":
                self._handle_device_hearbeat(device_id,payload)
            elif message_type == "command" and len(topic_parts) > 3 and topic_parts[3] == "response":
                self._handle_command_response(device_id, payload)
            elif message_type == "firmware" and len(topic_parts) > 3 and topic_parts[3] == "status":
                self._handle_firmware_status(device_id, payload)
            else:
                logger.warning(f"Unknown message type: {message_type}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_device_data(self, device_id, payload:str):
        """处理设备数据上报"""
        try:
            data = json.loads(payload)
            db = SessionLocal()
            try:
                device_data = DeviceDataCreate(
                    device_id=device_id,
                    data_type=data.get("type","telemetry"),
                    data=data.get("data",{}),
                    quality=data.get("quality","good")
                )
                device_data_crud.create(db, obj_in=device_data)
                logger.info(f"Saved device data: {device_id}")
            finally:
                db.close()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in device data: {payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_device_status(self, device_id, payload:str):
        """处理设备状态上报"""
        try:
            status_data = json.loads(payload)
            status = status_data.get("status", "unknown")
            db = SessionLocal()
            try:
                device = device_crud.update_status(db, device_id, status)
                if device:
                    logger.info(f"Updated status for device {device_id}:{status}")
                else:
                    logger.warning(f"Device not found: {device_id}")
            finally:
                db.close()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in device status: {payload}")
        except Exception as e:
            logger.error(f"Error handling device status: {e}")

    def _handle_device_hearbeat(self, device_id:str, payload:str):
        try:
            db = SessionLocal()
            try:
                device = device_crud.update_status(db, device_id, "online")
                if device:
                    logger.debug(f"Heartbeat received from device {device_id}")
                else:
                    logger.warning(f"Device not found: {device_id}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error handling device heartbeat: {e}")

    def _handle_command_response(self, device_id, payload:str):
        """处理命令响应"""
        try:
            response_data = json.loads(payload)
            command_id = response_data.get("command_id")
            status = response_data.get("status", "acknowledged")
            result = response_data.get("result")
            if command_id:
                db = SessionLocal()
                try:
                    device_command_crud.update_status(
                        db, command_id, status, {"result": result}
                    )
                    logger.info(f"Updated command {command_id} status:{status}")
                finally:
                    db.close()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in command response: {payload}")
        except Exception as e:
            logger.error(f"Error handling command response: {e}")

    def _handle_firmware_status(self, device_id, payload:str):
        """处理固件升级状态"""
        try:
            status_data = json.loads(payload)
            # 这里可以更新固件升级任务的状态
            # 具体实现依赖于固件升级模块
            logger.info(f"Firmware status from device {device_id}:{status_data}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in firmware status: {payload}")
        except Exception as e:
            logger.error(f"Error handling firmware status: {e}")

    def start(self):
        """启动MQTT客户端"""
        try:
            self.client = mqtt.Client(client_id="iot_backend_service")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            # 设置认证信息
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME,settings.MQTT_PASSWORD)
            # 连接到MQTT代理
            self.client.connect(settings.MQTT_BROKER_HOST,settings.MQTT_BROKER_PORT, 60)
            # 启动网络循环
            self.client.loop_start()
            logger.info("MQTT service started")
        except Exception as e:
            logger.error(f"Failed to start MQTT service: {e}")

    def stop(self):
        """停止MQTT客户端"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT service stopped")

    def publish(self, topic: str, payload: str, qos: int = 1):
        """发布消息"""
        if self.client and self.connected:
            try:
                result = self.client.publish(topic, payload, qos)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Published message to {topic}")
                else:
                    logger.error(f"Failed to publish message to {topic}, errorcode: {result.rc}")
            except Exception as e:
                logger.error(f"Error publishing message: {e}")
        else:
            logger.error("MQTT client not connected")


# 全局MQTT服务实例
mqtt_service = MQTTService()
# 为了向后兼容，保留mqtt_client引用
mqtt_client = mqtt_service

# # MQTT 客户端实例
# mqtt_client = mqtt.Client(client_id="backend_service")
#
#
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("Connected to MQTT Broker!")
#         # 订阅设备数据上报主题
#         client.subscribe("device/+/data")
#         client.subscribe("device/+/status")
#     else:
#         print(f"Failed to connect, return code {rc}\n")
#
#
# def on_message(client, userdata, msg):
#     print(f"Received message: {msg.topic} {msg.payload.decode()}")
#     topic_parts = msg.topic.split('/')
#     device_id = topic_parts[1]
#     message_type = topic_parts[2]
#     db = SessionLocal()
#     try:
#         if message_type == "data":
#             payload = json.loads(msg.payload.decode())
#             device_data = DeviceDataCreate(device_id=device_id, data=payload)
#             device_crud.record_device_data(db, device_data)
#             # 可以在这里触发Celery任务进行数据处理或告警
#         elif message_type == "status":
#             status_payload = json.loads(msg.payload.decode())
#             db_device = device_crud.get_device_by_unique_id(db, device_id)
#         if db_device:
#             device_crud.update_device(db, db_device,DeviceUpdate(status=status_payload.get("status")))
#     except Exception as e:
#         print(f"Error processing MQTT message: {e}")
#     finally:
#         db.close()
#
#
# def start_mqtt_client():
#     mqtt_client.on_connect = on_connect
#     mqtt_client.on_message = on_message
#     mqtt_client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
#     mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT,60)
#     mqtt_client.loop_start() # 在后台线程运行，处理网络流量、回调等
#     # 在FastAPI启动时调用 start_mqtt_client()
#     # 在FastAPI关闭时调用 mqtt_client.loop_stop() 和 mqtt_client.disconnect()