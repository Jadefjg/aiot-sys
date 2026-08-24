# Redis事件发布器

import json
import logging
import redis
from typing import Any, Dict, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Redis事件发布器 - 用于发布设备事件到其他微服务"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False

    def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            self.connected = False
            logger.error(f"Failed to connect to Redis: {e}")

    def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            self.redis_client.close()
            self.connected = False
            logger.info("Disconnected from Redis")

    def publish_event(self, channel: str, event_data: Dict[str, Any]) -> bool:
        """发布事件到指定通道"""
        if not self.connected or not self.redis_client:
            logger.error("Redis not connected, cannot publish event")
            return False

        try:
            # 添加时间戳
            event_data["timestamp"] = datetime.utcnow().isoformat()
            message = json.dumps(event_data, ensure_ascii=False)
            self.redis_client.publish(channel, message)
            logger.debug(f"Published event to {channel}: {message[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")
            return False

    def publish_device_data(self, device_id: str, data_type: str, data: Dict[str, Any], quality: str = "good"):
        """发布设备数据事件"""
        event_data = {
            "event_type": "device_data",
            "device_id": device_id,
            "data_type": data_type,
            "data": data,
            "quality": quality
        }
        return self.publish_event(settings.EVENT_CHANNEL_DEVICE_DATA, event_data)

    def publish_device_status(self, device_id: str, status: str, extra_data: Optional[Dict] = None):
        """发布设备状态变更事件"""
        event_data = {
            "event_type": "device_status",
            "device_id": device_id,
            "status": status
        }
        if extra_data:
            event_data.update(extra_data)
        return self.publish_event(settings.EVENT_CHANNEL_DEVICE_STATUS, event_data)

    def publish_device_heartbeat(self, device_id: str):
        """发布设备心跳事件"""
        event_data = {
            "event_type": "device_heartbeat",
            "device_id": device_id
        }
        return self.publish_event(settings.EVENT_CHANNEL_DEVICE_HEARTBEAT, event_data)

    def publish_command_response(self, device_id: str, command_id: str, status: str, result: Optional[Dict] = None):
        """发布命令响应事件"""
        event_data = {
            "event_type": "command_response",
            "device_id": device_id,
            "command_id": command_id,
            "status": status,
            "result": result
        }
        return self.publish_event(settings.EVENT_CHANNEL_COMMAND_RESPONSE, event_data)

    def publish_firmware_status(self, device_id: str, task_id: str, status: str, progress: int = 0, error: Optional[str] = None):
        """发布固件升级状态事件"""
        event_data = {
            "event_type": "firmware_status",
            "device_id": device_id,
            "task_id": task_id,
            "status": status,
            "progress": progress
        }
        if error:
            event_data["error"] = error
        return self.publish_event(settings.EVENT_CHANNEL_FIRMWARE_STATUS, event_data)


# 全局事件发布器实例
event_publisher = EventPublisher()
