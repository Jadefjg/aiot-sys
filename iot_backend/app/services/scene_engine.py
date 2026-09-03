"""云端场景执行：属性上报触发条件评估并下发动作"""
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.crud.device import device_crud
from app.crud.group import binding_crud, scene_crud
from app.db.models.smart import Scene

logger = logging.getLogger(__name__)

OPS = {
    "=": lambda a, b: a == b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _compare(left, operator: str, right) -> bool:
    fn = OPS.get(operator or "==")
    return bool(fn and fn(_to_number(left), _to_number(right)))


def _in_time_window(scene: Scene) -> bool:
    now = datetime.utcnow()
    if scene.weekdays and now.weekday() not in scene.weekdays:
        return False
    window = scene.time_range or {}
    start, end = window.get("start"), window.get("end")
    if start and end:
        current = now.strftime("%H:%M")
        if not (start <= current <= end):
            return False
    return True


def _match_rule(rule: dict, device_id: str, values: Dict[str, Any], product_id: str = None) -> bool:
    target = rule.get("device_id")
    if target and target != device_id:
        return False
    want_product = rule.get("product_id")
    if want_product and want_product != product_id:
        return False
    field = rule.get("property") or rule.get("field")
    if not field:
        return True
    if field not in values:
        return False
    return _compare(values.get(field), rule.get("operator") or ">", rule.get("value"))


def _publish(device, action: str, payload: dict) -> None:
    from app.services.mqtt_service import mqtt_client
    from app.services.device_runtime_service import device_runtime

    body = {"msg_id": str(uuid.uuid4()), "device_id": device.device_id, **payload}
    mqtt_client.publish(device_runtime._target_topic(device, action), json.dumps(body))


class SceneEngine:
    """属性变化 → 场景/联动（MQTT 异步下发，不阻塞上报线程）"""

    def __init__(self):
        self._echo_until = {}
        self._scene_until = {}
        self._scenes = []
        self._bindings = []
        self._cache_at = 0.0

    def invalidate(self) -> None:
        self._cache_at = 0.0

    def on_device_values(self, db: Session, device_id: str, changed: dict, merged: dict) -> None:
        self._refresh(db)
        self._run_scenes(db, device_id, merged)
        self._run_bindings(db, device_id, changed)

    def _refresh(self, db: Session) -> None:
        now = time.time()
        if now - self._cache_at > 3:
            self._scenes = scene_crud.get_multi(db, limit=500)
            self._bindings = binding_crud.get_multi(db, limit=500)
            self._cache_at = now

    def _run_scenes(self, db: Session, device_id: str, values: dict) -> None:
        device = device_crud.get_by_device_id(db, device_id)
        product_id = device.product_id if device else None
        now = time.time()
        for scene in self._scenes:
            if not scene.enabled or not _in_time_window(scene):
                continue
            cooldown_key = (scene.id, device_id)
            if self._scene_until.get(cooldown_key, 0) > now:
                continue
            triggers = scene.triggers or []
            if triggers and not any(_match_rule(t, device_id, values, product_id) for t in triggers):
                continue
            conditions = scene.conditions or []
            if conditions and not all(_match_rule(c, device_id, values, product_id) for c in conditions):
                continue
            self._scene_until[cooldown_key] = now + 8
            self._execute_actions(db, scene.actions or [], device_id)

    def _run_bindings(self, db: Session, device_id: str, changed: dict) -> None:
        now = time.time()
        if self._echo_until.get(device_id, 0) > now:
            return
        for binding in self._bindings:
            if not binding.enabled:
                continue
            peer = None
            if binding.device1_id == device_id:
                peer = binding.device2_id
            elif binding.bidirectional and binding.device2_id == device_id:
                peer = binding.device1_id
            if not peer:
                continue
            other = device_crud.get_by_device_id(db, peer)
            current = (other.values or {}) if other else {}
            delta = {k: v for k, v in changed.items() if current.get(k) != v}
            if delta:
                self._echo_until[peer] = now + 1.5
                self._write_device(db, peer, delta)

    def _execute_actions(self, db: Session, actions: List[dict], source_device_id: str = "") -> None:
        for action in actions:
            kind = action.get("type") or "write"
            target = action.get("device_id") or source_device_id
            if not target:
                continue
            if kind == "write":
                self._write_device(db, target, action.get("values") or action.get("data") or {})
            elif kind == "action":
                self._invoke(db, target, action.get("action") or "default", action.get("params") or {})

    def _write_device(self, db: Session, device_id: str, values: dict) -> None:
        device = device_crud.get_by_device_id(db, device_id)
        if device and values:
            _publish(device, "write", {"values": values})

    def _invoke(self, db: Session, device_id: str, action: str, params: dict) -> None:
        device = device_crud.get_by_device_id(db, device_id)
        if device:
            _publish(device, "action", {"action": action, "params": params})


scene_engine = SceneEngine()
