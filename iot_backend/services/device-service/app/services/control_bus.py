"""通过 mqtt-gateway gRPC 下发，经 Redis 队列等待设备响应"""
import json
import logging
import uuid
from typing import Any, Dict

from app.core.config import settings
from app.core.redis import get_redis
from app.db.models.device import Device
from app.grpc.clients.mqtt_client import mqtt_grpc_client
from app.services.device_runtime_service import device_runtime

logger = logging.getLogger(__name__)


def request_device(device: Device, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """HTTP → gRPC Publish → MQTT → Redis 响应队列"""
    msg_id = str(uuid.uuid4())
    body = {**payload, "msg_id": msg_id, "device_id": device.device_id}
    topic = device_runtime.target_topic(device, action)
    ok, err = mqtt_grpc_client.publish_message(topic, json.dumps(body, ensure_ascii=False))
    if not ok:
        raise ConnectionError(err or "MQTT Gateway 发布失败")

    key = f"{settings.CONTROL_RESP_PREFIX}{msg_id}"
    popped = get_redis().blpop(key, timeout=settings.CONTROL_TIMEOUT)
    if not popped:
        raise TimeoutError(f"设备响应超时({settings.CONTROL_TIMEOUT}s): {action}")
    _, raw = popped
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
