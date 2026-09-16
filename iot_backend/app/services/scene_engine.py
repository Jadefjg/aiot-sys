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
    if not fn:
        return False
    try:
        return bool(fn(_to_number(left), _to_number(right)))
    except TypeError:
        return False


def _in_time_window(scene: Scene) -> bool:
    now = datetime.utcnow()
    if scene.weekdays and now.weekday() not in scene.weekdays:
        return False
    window = scene.time_range or {}
    start, end = window.get("start"), window.get("end")
    if start and end:
        current = now.strftime("%H:%M")
        # Support windows crossing midnight (e.g. 23:00-02:00).
        if start <= end:
            inside = start <= current <= end
        else:
            inside = current >= start or current <= end
        if not inside:
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


def _publish(device, action: str, payload: dict) -> bool:
    from app.services.mqtt_service import mqtt_client
    from app.services.device_runtime_service import device_runtime

    body = {"msg_id": str(uuid.uuid4()), "device_id": device.device_id, **payload}
    return mqtt_client.publish(device_runtime._target_topic(device, action), json.dumps(body))


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

    def on_alarm_event(self, db: Session, device_id: str, event: dict) -> None:
        """Evaluate explicit alarm/recovery scene triggers."""
        self._refresh(db)
        for scene in self._scenes:
            if not scene.enabled:
                continue
            for trigger in scene.triggers or []:
                trigger_type = trigger.get("type") or trigger.get("event")
                if trigger_type not in ("alarm", "alarm_recovery", "recovery"):
                    continue
                wanted = trigger.get("validator_name") or trigger.get("validator")
                if wanted and wanted != event.get("validator_name"):
                    continue
                if trigger_type in ("alarm_recovery", "recovery") and not event.get("resolved"):
                    continue
                if trigger_type == "alarm" and event.get("resolved"):
                    continue
                self._execute_scene(db, scene, device_id, event)
                break

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
            if scene.delay_seconds:
                try:
                    from celery_worker import execute_scene_task
                    execute_scene_task.apply_async(
                        args=[scene.id, device_id, values],
                        countdown=max(0, min(int(scene.delay_seconds), 300)),
                    )
                except Exception as exc:
                    logger.exception("Failed to enqueue scene %s: %s", scene.id, exc)
                    self._execute_scene(db, scene, device_id, values)
            else:
                self._execute_scene(db, scene, device_id, values)

    def _execute_scene(self, db, scene, source_device_id, trigger_data):
        from app.db.models.smart import SceneExecution
        execution = SceneExecution(scene_id=scene.id, source_device_id=source_device_id,
            trigger_data=trigger_data, actions=scene.actions or [], status="running")
        db.add(execution); db.commit(); db.refresh(execution)
        # delay_seconds is a supported schema field; honor it before actions.
        # Keep the delay bounded so a malformed scene cannot stall ingestion.
        errors = []
        attempts = max(1, int(scene.max_retries or 0) + 1)
        for attempt in range(attempts):
            execution.attempt_count = attempt + 1
            errors = self._execute_actions(db, scene.actions or [], source_device_id)
            if not errors:
                break
            time.sleep(min(2 ** attempt, 5))
        execution.status = "success" if not errors else "failed"
        execution.error_message = "; ".join(errors) if errors else None
        execution.finished_at = datetime.utcnow()
        db.add(execution); db.commit()

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

    def _execute_actions(self, db: Session, actions: List[dict], source_device_id: str = "") -> List[str]:
        errors = []
        for action in actions:
            kind = action.get("type") or "write"
            target = action.get("device_id") or source_device_id
            if not target:
                continue
            if kind == "write":
                if not self._write_device(db, target, action.get("values") or action.get("data") or {}):
                    errors.append(f"write:{target}")
            elif kind == "action":
                if not self._invoke(db, target, action.get("action") or "default", action.get("params") or {}):
                    errors.append(f"action:{target}")
        return errors

    def _write_device(self, db: Session, device_id: str, values: dict) -> bool:
        device = device_crud.get_by_device_id(db, device_id)
        if device and values:
            return _publish(device, "write", {"values": values})
        return False

    def _invoke(self, db: Session, device_id: str, action: str, params: dict) -> bool:
        device = device_crud.get_by_device_id(db, device_id)
        if device:
            return _publish(device, "action", {"action": action, "params": params})
        return False


scene_engine = SceneEngine()
