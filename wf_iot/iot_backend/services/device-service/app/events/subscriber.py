# Redis事件订阅器

import json
import logging
import threading
import redis
from typing import Optional

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_crud, device_data_crud, device_command_crud
from app.schemas.device import DeviceDataCreate

logger = logging.getLogger(__name__)


class EventSubscriber:
    """Redis事件订阅器 - 监听MQTT Gateway发布的设备事件"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")

    def disconnect(self):
        """断开Redis连接"""
        self.running = False
        if self.pubsub:
            self.pubsub.unsubscribe()
            self.pubsub.close()
        if self.redis_client:
            self.redis_client.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("Disconnected from Redis")

    def start(self):
        """开始订阅事件"""
        if not self.pubsub:
            logger.error("Redis not connected")
            return

        # 订阅事件通道
        channels = [
            settings.EVENT_CHANNEL_DEVICE_DATA,
            settings.EVENT_CHANNEL_DEVICE_STATUS,
            settings.EVENT_CHANNEL_DEVICE_HEARTBEAT,
            settings.EVENT_CHANNEL_COMMAND_RESPONSE
        ]
        self.pubsub.subscribe(**{channel: self._handle_message for channel in channels})

        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        logger.info(f"Started listening on channels: {channels}")

    def _listen(self):
        """监听消息循环"""
        while self.running:
            try:
                message = self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    self._handle_message(message)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")

    def _handle_message(self, message):
        """处理接收到的消息"""
        if message is None or message.get('type') != 'message':
            return

        try:
            channel = message.get('channel', '')
            data = json.loads(message.get('data', '{}'))
            event_type = data.get('event_type', '')

            logger.debug(f"Received event on {channel}: {event_type}")

            if event_type == 'device_data':
                self._handle_device_data(data)
            elif event_type == 'device_status':
                self._handle_device_status(data)
            elif event_type == 'device_heartbeat':
                self._handle_device_heartbeat(data)
            elif event_type == 'command_response':
                self._handle_command_response(data)
            else:
                logger.warning(f"Unknown event type: {event_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in event message")
        except Exception as e:
            logger.error(f"Error handling event: {e}")

    def _handle_device_data(self, data: dict):
        """处理设备数据事件"""
        device_id = data.get('device_id')
        data_type = data.get('data_type', 'telemetry')
        sensor_data = data.get('data', {})
        quality = data.get('quality', 'good')

        if not device_id:
            return

        db = SessionLocal()
        try:
            device_data = DeviceDataCreate(
                device_id=device_id,
                data_type=data_type,
                data=sensor_data,
                quality=quality
            )
            result = device_data_crud.create(db, device_data)
            if result:
                logger.info(f"Saved device data for {device_id}")
            else:
                logger.warning(f"Device not found: {device_id}")
        except Exception as e:
            logger.error(f"Error saving device data: {e}")
        finally:
            db.close()

    def _handle_device_status(self, data: dict):
        """处理设备状态事件"""
        device_id = data.get('device_id')
        status = data.get('status')

        if not device_id or not status:
            return

        db = SessionLocal()
        try:
            device = device_crud.update_status(db, device_id, status)
            if device:
                logger.info(f"Updated status for {device_id}: {status}")
            else:
                logger.warning(f"Device not found: {device_id}")
        except Exception as e:
            logger.error(f"Error updating device status: {e}")
        finally:
            db.close()

    def _handle_device_heartbeat(self, data: dict):
        """处理设备心跳事件"""
        device_id = data.get('device_id')

        if not device_id:
            return

        db = SessionLocal()
        try:
            device = device_crud.update_status(db, device_id, "online")
            if device:
                logger.debug(f"Heartbeat from {device_id}")
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
        finally:
            db.close()

    def _handle_command_response(self, data: dict):
        """处理命令响应事件"""
        command_id = data.get('command_id')
        status = data.get('status', 'acknowledged')
        result = data.get('result')

        if not command_id:
            return

        db = SessionLocal()
        try:
            command = device_command_crud.update_status(db, int(command_id), status, result)
            if command:
                logger.info(f"Updated command {command_id} status: {status}")
        except Exception as e:
            logger.error(f"Error updating command status: {e}")
        finally:
            db.close()


# 全局事件订阅器实例
event_subscriber = EventSubscriber()
