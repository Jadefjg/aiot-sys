"""规则引擎：属性条件命中后执行告警/Webhook/MQTT/写点"""
import json
import logging
import time
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.crud.alarm import alarm_crud
from app.crud.channel import rule_crud
from app.crud.device import device_crud
from app.schemas.alarm import AlarmCreate

logger = logging.getLogger(__name__)

OPS = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


class RuleEngine:
    """条件由假变真时触发一次，避免遥测刷屏。"""

    def __init__(self):
        self._active = {}
        self._cache = []
        self._cache_at = 0.0

    def invalidate(self) -> None:
        self._cache_at = 0.0

    def on_values(self, db: Session, device, changed: dict, merged: dict, publish_alarm=None) -> None:
        now = time.time()
        if now - self._cache_at > 3:
            self._cache = rule_crud.get_enabled(db)
            self._cache_at = now
        for rule in self._cache:
            if rule.device_id and rule.device_id != device.device_id:
                continue
            if rule.product_id and rule.product_id != device.product_id:
                continue
            hit = self._matched(rule, merged)
            key = (rule.id, device.device_id)
            if not hit:
                self._active.pop(key, None)
                continue
            if self._active.get(key):
                continue
            self._active[key] = True
            self._run_actions(db, device, rule, merged, publish_alarm)

    def _matched(self, rule, merged: dict) -> bool:
        field = rule.field
        if not field:
            return True
        if field not in merged:
            return False
        op = OPS.get(rule.operator or ">")
        if not op:
            return False
        return bool(op(_num(merged.get(field)), _num(rule.value)))

    def _run_actions(self, db: Session, device, rule, values: dict, publish_alarm) -> None:
        for action in rule.actions or [{"type": "alarm"}]:
            kind = action.get("type") or "alarm"
            if kind == "alarm":
                alarm = alarm_crud.create(
                    db,
                    AlarmCreate(
                        device_id=device.id,
                        product_id=device.product_id,
                        title=action.get("title") or rule.name,
                        message=action.get("message") or f"{rule.field} {rule.operator} {rule.value}",
                        level=action.get("level") or "warning",
                        validator_name=f"rule:{rule.id}",
                    ),
                )
                if publish_alarm:
                    publish_alarm(device.device_id, {
                        "id": alarm.id, "title": alarm.title, "message": alarm.message, "level": alarm.level
                    })
            elif kind == "mqtt":
                self._mqtt(action.get("topic") or f"rule/{rule.id}/hit", {
                    "device_id": device.device_id, "rule": rule.name, "values": values
                })
            elif kind == "webhook":
                self._webhook(action.get("url"), {"device_id": device.device_id, "rule": rule.name, "values": values})
            elif kind == "write":
                self._write(db, action.get("device_id") or device.device_id, action.get("values") or {})

    def _mqtt(self, topic: str, payload: Dict[str, Any]) -> None:
        from app.services.mqtt_service import mqtt_client
        mqtt_client.publish(topic, json.dumps(payload, default=str))

    def _webhook(self, url: str, payload: dict) -> None:
        from app.services.http_dispatch import post_json
        post_json(url, payload)

    def _write(self, db: Session, device_id: str, values: dict) -> None:
        import uuid
        from app.services.mqtt_service import mqtt_client
        from app.services.device_runtime_service import device_runtime

        device = device_crud.get_by_device_id(db, device_id)
        if not device or not values:
            return
        body = {"msg_id": str(uuid.uuid4()), "device_id": device_id, "values": values}
        mqtt_client.publish(device_runtime._target_topic(device, "write"), json.dumps(body))


rule_engine = RuleEngine()
