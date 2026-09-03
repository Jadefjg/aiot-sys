"""MQTT 服务：设备生命周期 + 连接/协议总线分发"""
import json
import logging
import os
import threading
import time
from queue import Empty, Full, Queue
from typing import Callable, List, Optional, Union

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_command_crud, device_crud, device_data_crud
from app.schemas.device import DeviceDataCreate, DeviceUpdate
from app.services.device_runtime_service import device_runtime

logger = logging.getLogger(__name__)

DEVICE_TOPICS = [
    "device/+/data", "device/+/values", "device/+/property",
    "device/+/status", "device/+/online", "device/+/offline",
    "device/+/register", "device/+/location", "device/+/error",
    "device/+/event", "device/+/log", "device/+/heartbeat",
    "device/+/command/response", "device/+/sync/response",
    "device/+/read/response", "device/+/write/response",
    "device/+/action/response", "device/+/setting/response",
    "device/+/firmware/status", "push/+/values",
    "link/+/+/open", "link/+/+/close", "link/+/+/up", "link/+/+/down",
    "protocol/+/+/+/open", "protocol/+/+/+/close", "protocol/+/+/+/up",
    "protocol/+/+/+/poll", "protocol/+/+/+/sync",
    "protocol/+/+/+/read", "protocol/+/+/+/write", "protocol/+/+/+/action",
]

PayloadHandler = Callable[[str, bytes], None]


class MQTTService:
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self._handlers: List[tuple] = []
        self._queue: Queue = Queue(maxsize=4000)
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None

    def register_handler(self, prefix: str, handler: PayloadHandler) -> None:
        """插件订阅：按主题前缀分发原始载荷"""
        self._handlers.append((prefix, handler))

    def on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            self.connected = False
            logger.error("Failed to connect to MQTT broker, rc=%s", rc)
            return
        self.connected = True
        logger.info("Connected to MQTT broker")
        for topic in DEVICE_TOPICS:
            client.subscribe(topic)

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.warning("Disconnected from MQTT broker, rc=%s", rc)

    def on_message(self, client, userdata, msg):
        """Paho 回调只做入队；控制响应立刻唤醒 HTTP 等待"""
        try:
            topic = msg.topic
            payload = bytes(msg.payload or b"")
            parts = topic.split("/")
            if len(parts) >= 4 and parts[0] == "device" and parts[-1] == "response":
                self._handle_response(payload.decode("utf-8", errors="replace"))
            try:
                self._queue.put_nowait((topic, payload))
            except Full:
                logger.warning("MQTT queue full, drop %s", topic)
        except Exception as exc:
            logger.error("Error queueing MQTT message: %s", exc)

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                topic, payload = self._queue.get(timeout=0.4)
            except Empty:
                continue
            try:
                self._process(topic, payload)
            except Exception as exc:
                logger.error("Error processing MQTT message: %s", exc)

    def _process(self, topic: str, payload: bytes) -> None:
        matched = False
        for prefix, handler in self._handlers:
            if topic.startswith(prefix):
                handler(topic, payload)
                matched = True
        if matched and not topic.startswith("device/"):
            return
        parts = topic.split("/")
        if parts[0] == "push" and len(parts) >= 3:
            self._handle_push(parts[1], payload)
            return
        if len(parts) < 3 or parts[0] != "device":
            return
        device_id, message_type = parts[1], parts[2]
        suffix = parts[3] if len(parts) > 3 else None
        raw = payload.decode("utf-8", errors="replace")
        if suffix == "response":
            if message_type == "command":
                self._handle_legacy_command(device_id, raw)
            return
        self._dispatch(device_id, message_type, raw)

    def _dispatch(self, device_id: str, message_type: str, raw: str):
        handlers = {
            "data": self._handle_values,
            "values": self._handle_values,
            "property": self._handle_values,
            "status": self._handle_status,
            "online": lambda d, _: self._set_online(d, True),
            "offline": lambda d, _: self._set_online(d, False),
            "register": self._handle_register,
            "location": self._handle_location,
            "error": self._handle_error,
            "event": self._handle_event,
            "log": self._handle_event,
            "heartbeat": lambda d, _: self._set_online(d, True),
            "firmware": self._handle_firmware,
        }
        handler = handlers.get(message_type)
        if handler:
            handler(device_id, raw)

    def _parse(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON: %s", raw)
            return {}

    def _handle_values(self, device_id: str, raw: str):
        data = self._parse(raw)
        if not data and raw and raw.strip():
            values = {"raw": raw}
        else:
            values = data.get("data") if isinstance(data.get("data"), dict) else data
            if not isinstance(values, dict):
                values = {"raw": raw}
        db = SessionLocal()
        try:
            device_runtime.put_values(
                db, device_id, values, publish_alarm=self._publish_alarm
            )
        finally:
            db.close()

    def _handle_status(self, device_id: str, raw: str):
        self._set_online(device_id, self._parse(raw).get("status") == "online")

    def _set_online(self, device_id: str, online: bool, _raw: str = ""):
        db = SessionLocal()
        try:
            device_runtime.set_online(db, device_id, online)
        finally:
            db.close()

    def _handle_register(self, device_id: str, raw: str):
        data = self._parse(raw)
        db = SessionLocal()
        try:
            from app.crud.product import product_crud

            device = device_runtime.register(
                db,
                device_id,
                product_id=data.get("product_id"),
                device_name=data.get("device_name"),
                gateway_id=data.get("gateway_id"),
            )
            product = product_crud.get_by_product_id(db, device.product_id)
            if product:
                self.publish(f"product/{product.product_id}/model", json.dumps(product.model or {}))
                if product.config:
                    for name, cfg in (product.config or {}).items():
                        self.publish(
                            f"product/{product.product_id}/config/{name}",
                            json.dumps(cfg if not isinstance(cfg, str) else {"value": cfg}),
                        )
        finally:
            db.close()

    def _handle_location(self, device_id: str, raw: str):
        data = self._parse(raw)
        lat, lng = data.get("latitude"), data.get("longitude")
        if lat is None or lng is None:
            return
        db = SessionLocal()
        try:
            device_runtime.set_location(db, device_id, float(lat), float(lng), data.get("geo_code"))
        finally:
            db.close()

    def _handle_error(self, device_id: str, raw: str):
        data = self._parse(raw)
        msg = data.get("error") or data.get("message") or raw
        db = SessionLocal()
        try:
            device_runtime.set_error(db, device_id, str(msg))
        finally:
            db.close()

    def _handle_event(self, device_id: str, raw: str):
        data = self._parse(raw) or {"message": raw}
        db = SessionLocal()
        try:
            device_data_crud.create(
                db,
                DeviceDataCreate(device_id=device_id, data=data, data_type="event"),
            )
            if isinstance(data, dict):
                try:
                    from app.services.media_service import record_event
                    record_event(db, device_id, data)
                except Exception as exc:
                    logger.warning("media event skipped: %s", exc)
        finally:
            db.close()

    def _handle_push(self, device_id: str, payload: bytes):
        """push/{id}/values 是属性上报，不是事件"""
        self._handle_values(device_id, payload.decode("utf-8", errors="replace"))

    def _handle_firmware(self, device_id: str, raw: str):
        data = self._parse(raw)
        try:
            task_id = int(data.get("task_id"))
        except (TypeError, ValueError):
            logger.info("Firmware status %s: %s", device_id, raw)
            return
        status = data.get("status") or "in_progress"
        progress = data.get("progress")
        error = data.get("error") or data.get("error_message")
        db = SessionLocal()
        try:
            from app.crud.firmware import firmware_upgrade_task_crud

            if status in ("success", "failed", "cancelled", "in_progress", "pending"):
                firmware_upgrade_task_crud.update_status(
                    db, task_id, status,
                    progress=int(progress) if progress is not None else None,
                    error_message=error,
                )
            elif progress is not None:
                firmware_upgrade_task_crud.update_progress(db, task_id, int(progress))
            version = data.get("firmware_version") or data.get("version")
            if status == "success" and version:
                device = device_crud.get_by_device_id(db, device_id)
                if device:
                    device_crud.update(db, device, DeviceUpdate(firmware_version=str(version)))
        finally:
            db.close()

    def _handle_response(self, raw: str):
        device_runtime.on_response(self._parse(raw))

    def _handle_legacy_command(self, device_id: str, raw: str):
        data = self._parse(raw)
        try:
            command_id = int(data.get("command_id"))
        except (TypeError, ValueError):
            command_id = None
        if not command_id:
            self._handle_response(raw)
            return
        db = SessionLocal()
        try:
            device_command_crud.update_status(
                db, command_id, data.get("status", "acknowledged"), {"result": data.get("result")}
            )
        finally:
            db.close()

    def _publish_alarm(self, device_id: str, alarm: dict):
        self.publish(f"device/{device_id}/alarm", json.dumps(alarm))

    def _connect(self) -> bool:
        try:
            self._stop.clear()
            if not (self._worker and self._worker.is_alive()):
                self._worker = threading.Thread(target=self._worker_loop, daemon=True)
                self._worker.start()
            self.client = mqtt.Client(client_id="iot_backend_service")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            logger.info("MQTT service started")
            return True
        except Exception as exc:
            logger.error("Failed to start MQTT service: %s", exc)
            return False

    async def start(self) -> bool:
        return self._connect()

    async def stop(self) -> bool:
        self._stop.set()
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT service stopped")
        self.connected = False
        return True

    def publish(self, topic: str, payload: Union[str, bytes, dict], qos: int = 1) -> bool:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if self.client and self.connected:
            return self._publish_connected(topic, payload, qos)
        return self._publish_once(topic, payload, qos)

    def _publish_connected(self, topic: str, payload, qos: int) -> bool:
        try:
            result = self.client.publish(topic, payload, qos)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error("Publish failed %s rc=%s", topic, result.rc)
                return False
            return True
        except Exception as exc:
            logger.error("Error publishing: %s", exc)
            return False

    def _publish_once(self, topic: str, payload, qos: int) -> bool:
        """未订阅进程（如 Celery）短连接只发不订，避免与 backend 重复消费"""
        client = mqtt.Client(client_id=f"iot-pub-{os.getpid()}")
        try:
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 10)
            result = client.publish(topic, payload, qos)
            deadline = time.time() + 5
            while time.time() < deadline:
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logger.error("One-shot publish failed %s rc=%s", topic, result.rc)
                    return False
                client.loop(timeout=0.2)
                if result.is_published():
                    return True
            logger.error("One-shot publish timeout %s", topic)
            return False
        except Exception as exc:
            logger.error("MQTT publish failed: %s", exc)
            return False
        finally:
            try:
                client.disconnect()
            except Exception:
                pass


mqtt_service = MQTTService()
mqtt_client = mqtt_service
