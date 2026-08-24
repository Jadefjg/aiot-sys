# MQTT客户端服务

import json
import logging
import uuid
import paho.mqtt.client as mqtt
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.events.publisher import event_publisher

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT客户端 - 负责与MQTT Broker通信"""

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.connected_since: Optional[datetime] = None
        self.messages_published = 0
        self.messages_received = 0
        # 设备在线状态缓存
        self.device_online_status: Dict[str, Dict[str, Any]] = {}

    def on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.connected = True
            self.connected_since = datetime.utcnow()
            logger.info("Connected to MQTT broker")

            # 订阅设备相关主题
            topics = [
                ("device/+/data", 1),           # 设备数据上报
                ("device/+/status", 1),         # 设备状态上报
                ("device/+/command/response", 1),  # 命令响应
                ("device/+/heartbeat", 0),      # 设备心跳
                ("device/+/firmware/status", 1)  # 固件升级状态
            ]
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to topic: {topic}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")

    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            self.messages_received += 1
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.debug(f"Received message on topic: {topic}")

            # 解析主题
            topic_parts = topic.split("/")
            if len(topic_parts) < 3:
                logger.warning(f"Invalid topic format: {topic}")
                return

            device_id = topic_parts[1]
            message_type = topic_parts[2]

            # 更新设备在线状态
            self.device_online_status[device_id] = {
                "online": True,
                "last_seen": datetime.utcnow().isoformat()
            }

            # 处理不同类型的消息
            if message_type == "data":
                self._handle_device_data(device_id, payload)
            elif message_type == "status":
                self._handle_device_status(device_id, payload)
            elif message_type == "heartbeat":
                self._handle_device_heartbeat(device_id, payload)
            elif message_type == "command" and len(topic_parts) > 3 and topic_parts[3] == "response":
                self._handle_command_response(device_id, payload)
            elif message_type == "firmware" and len(topic_parts) > 3 and topic_parts[3] == "status":
                self._handle_firmware_status(device_id, payload)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _handle_device_data(self, device_id: str, payload: str):
        """处理设备数据上报 - 发布事件到Redis"""
        try:
            data = json.loads(payload)
            event_publisher.publish_device_data(
                device_id=device_id,
                data_type=data.get("type", "telemetry"),
                data=data.get("data", {}),
                quality=data.get("quality", "good")
            )
            logger.info(f"Published device data event for {device_id}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in device data: {payload}")
        except Exception as e:
            logger.error(f"Error handling device data: {e}")

    def _handle_device_status(self, device_id: str, payload: str):
        """处理设备状态上报 - 发布事件到Redis"""
        try:
            status_data = json.loads(payload)
            status = status_data.get("status", "unknown")
            event_publisher.publish_device_status(
                device_id=device_id,
                status=status,
                extra_data=status_data
            )
            logger.info(f"Published device status event for {device_id}: {status}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in device status: {payload}")
        except Exception as e:
            logger.error(f"Error handling device status: {e}")

    def _handle_device_heartbeat(self, device_id: str, payload: str):
        """处理设备心跳 - 发布事件到Redis"""
        try:
            event_publisher.publish_device_heartbeat(device_id=device_id)
            logger.debug(f"Published heartbeat event for {device_id}")
        except Exception as e:
            logger.error(f"Error handling device heartbeat: {e}")

    def _handle_command_response(self, device_id: str, payload: str):
        """处理命令响应 - 发布事件到Redis"""
        try:
            response_data = json.loads(payload)
            command_id = response_data.get("command_id")
            status = response_data.get("status", "acknowledged")
            result = response_data.get("result")

            if command_id:
                event_publisher.publish_command_response(
                    device_id=device_id,
                    command_id=command_id,
                    status=status,
                    result=result
                )
                logger.info(f"Published command response event for {device_id}, command: {command_id}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in command response: {payload}")
        except Exception as e:
            logger.error(f"Error handling command response: {e}")

    def _handle_firmware_status(self, device_id: str, payload: str):
        """处理固件升级状态 - 发布事件到Redis"""
        try:
            status_data = json.loads(payload)
            task_id = status_data.get("task_id", "")
            status = status_data.get("status", "unknown")
            progress = status_data.get("progress", 0)
            error = status_data.get("error")

            event_publisher.publish_firmware_status(
                device_id=device_id,
                task_id=task_id,
                status=status,
                progress=progress,
                error=error
            )
            logger.info(f"Published firmware status event for {device_id}: {status}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in firmware status: {payload}")
        except Exception as e:
            logger.error(f"Error handling firmware status: {e}")

    def start(self):
        """启动MQTT客户端"""
        try:
            self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message

            # 设置认证信息
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # 连接到MQTT代理
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)

            # 启动网络循环
            self.client.loop_start()
            logger.info(f"MQTT client started, connecting to {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

    def stop(self):
        """停止MQTT客户端"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT client stopped")

    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> tuple[bool, str]:
        """发布消息"""
        if not self.client or not self.connected:
            return False, "MQTT client not connected"

        try:
            result = self.client.publish(topic, payload, qos, retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.messages_published += 1
                message_id = str(uuid.uuid4())
                logger.info(f"Published message to {topic}")
                return True, message_id
            else:
                return False, f"Publish failed with error code: {result.rc}"
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False, str(e)

    def subscribe(self, topic: str, qos: int = 1) -> tuple[bool, str]:
        """订阅主题"""
        if not self.client or not self.connected:
            return False, "MQTT client not connected"

        try:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Subscribed to topic: {topic}")
                return True, ""
            else:
                return False, f"Subscribe failed with error code: {result[0]}"
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return False, str(e)

    def unsubscribe(self, topic: str) -> tuple[bool, str]:
        """取消订阅"""
        if not self.client or not self.connected:
            return False, "MQTT client not connected"

        try:
            result = self.client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Unsubscribed from topic: {topic}")
                return True, ""
            else:
                return False, f"Unsubscribe failed with error code: {result[0]}"
        except Exception as e:
            logger.error(f"Error unsubscribing from topic: {e}")
            return False, str(e)

    def get_device_online_status(self, device_ids: list[str]) -> Dict[str, Dict[str, Any]]:
        """获取设备在线状态"""
        result = {}
        for device_id in device_ids:
            if device_id in self.device_online_status:
                result[device_id] = self.device_online_status[device_id]
            else:
                result[device_id] = {"online": False, "last_seen": None}
        return result


# 全局MQTT客户端实例
mqtt_client = MQTTClient()
