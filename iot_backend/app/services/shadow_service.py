"""设备影子：desired / reported / delta；热数据走 Redis，MySQL 作持久化"""
import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.redis import get_redis
from app.crud.channel import shadow_crud

logger = logging.getLogger(__name__)
SHADOW_KEY = "iot:shadow:"
ONLINE_SET = "iot:online:devices"
SHADOW_TTL = 86400 * 7


def compute_delta(desired: Optional[dict], reported: Optional[dict]) -> Dict[str, Any]:
    """desired 有而 reported 缺失或不同的字段"""
    delta: Dict[str, Any] = {}
    for key, want in (desired or {}).items():
        if (reported or {}).get(key) != want:
            delta[key] = want
    return delta


def _cache_doc(device_id: str, doc: dict) -> None:
    client = get_redis()
    if not client:
        return
    try:
        client.setex(SHADOW_KEY + device_id, SHADOW_TTL, json.dumps(doc, default=str))
    except Exception as exc:
        logger.warning("shadow redis write: %s", exc)


def document(device_id: str, reported=None, desired=None, version: int = 0) -> dict:
    reported = reported or {}
    desired = desired or {}
    return {
        "device_id": device_id,
        "reported": reported,
        "desired": desired,
        "delta": compute_delta(desired, reported),
        "version": version,
    }


def to_document(obj) -> dict:
    if not obj:
        return document("", {}, {}, 0)
    return document(obj.device_id, obj.reported, obj.desired, obj.version or 0)


def cache_from_obj(obj) -> dict:
    doc = to_document(obj)
    _cache_doc(obj.device_id, doc)
    return doc


def set_online(device_id: str, online: bool) -> None:
    client = get_redis()
    if not client:
        return
    try:
        if online:
            client.sadd(ONLINE_SET, device_id)
        else:
            client.srem(ONLINE_SET, device_id)
    except Exception as exc:
        logger.warning("online set: %s", exc)


def is_online(device_id: str) -> bool:
    client = get_redis()
    if not client:
        return False
    try:
        return bool(client.sismember(ONLINE_SET, device_id))
    except Exception:
        return False


def online_count() -> int:
    client = get_redis()
    if not client:
        return 0
    try:
        return int(client.scard(ONLINE_SET) or 0)
    except Exception:
        return 0


def push_delta(device, delta: dict) -> None:
    if not device or not delta:
        return
    from app.services.device_runtime_service import device_runtime
    from app.services.mqtt_service import mqtt_client
    import uuid

    payload = {
        "msg_id": str(uuid.uuid4()),
        "device_id": device.device_id,
        "name": "shadow",
        "data": delta,
    }
    mqtt_client.publish(device_runtime._target_topic(device, "setting"), payload)
    mqtt_client.publish(f"$shadow/document/{device.device_id}/update/delta", payload)


def upsert_reported(db: Session, device_id: str, values: dict) -> dict:
    obj = shadow_crud.upsert_reported(db, device_id, values)
    return cache_from_obj(obj)


def set_desired(db: Session, device_id: str, desired: dict, device=None) -> dict:
    obj = shadow_crud.set_desired(db, device_id, desired)
    doc = cache_from_obj(obj)
    if device is not None and doc["delta"]:
        push_delta(device, doc["delta"])
    return doc


def sync_on_reconnect(db: Session, device) -> None:
    """设备上线后把未对齐的 desired 再推一次"""
    obj = shadow_crud.get(db, device.device_id)
    if not obj:
        return
    doc = cache_from_obj(obj)
    if doc["delta"]:
        push_delta(device, doc["delta"])
