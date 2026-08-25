"""设备运行时：属性上报、注册、远程控制请求-响应"""
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.crud.alarm import alarm_crud
from app.crud.device import device_crud, device_data_crud
from app.crud.product import product_crud
from app.db.models.device import Device
from app.schemas.alarm import AlarmCreate
from app.schemas.device import DeviceCreate, DeviceDataCreate, DeviceUpdate
from app.services.validator_service import evaluate_validators

logger = logging.getLogger(__name__)

# msg_id -> Event + 响应载荷
_pending: Dict[str, Dict[str, Any]] = {}
_pending_lock = threading.Lock()
DEFAULT_TIMEOUT = 30


class DeviceRuntimeService:
    """设备生命周期与控制中枢"""

    def register(
        self,
        db: Session,
        device_id: str,
        product_id: Optional[str] = None,
        device_name: Optional[str] = None,
        gateway_id: Optional[str] = None,
    ) -> Device:
        """设备注册：不存在则按产品自动建档并上线"""
        device = device_crud.get_by_device_id(db, device_id)
        if device:
            device_crud.update_status(db, device_id, "online")
            return device_crud.get_by_device_id(db, device_id)

        pid = product_id or "default"
        product = product_crud.get_by_product_id(db, pid)
        name = device_name or (product.name if product else device_id)
        device = device_crud.create(
            db,
            DeviceCreate(
                device_id=device_id,
                device_name=name,
                product_id=pid,
                gateway_id=gateway_id,
            ),
        )
        device_crud.update_status(db, device_id, "online")
        logger.info("自动注册设备 %s product=%s", device_id, pid)
        return device_crud.get_by_device_id(db, device_id)

    def set_online(self, db: Session, device_id: str, online: bool = True) -> Optional[Device]:
        status = "online" if online else "offline"
        device = device_crud.update_status(db, device_id, status)
        if device and not online and not device.gateway_id:
            # 网关离线时子设备一并离线
            children = (
                db.query(Device).filter(Device.gateway_id == device_id).all()
            )
            for child in children:
                child.status = "offline"
                db.add(child)
            db.commit()
        return device

    def put_values(
        self, db: Session, device_id: str, values: Dict[str, Any], publish_alarm=None
    ) -> Optional[Device]:
        """更新属性快照 → Validators → 写历史 → 刷新 online"""
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            device = self.register(db, device_id)
        if device.disabled:
            return device

        product = product_crud.get_by_product_id(db, device.product_id)
        try:
            from app.services.thing_parser import decode_values
            values = decode_values(product, values)
        except Exception as exc:
            logger.warning("Thing parser: %s", exc)

        merged = dict(device.values or {})
        merged.update(values)
        try:
            from app.services.thing_formula import apply_property_formulas
            props = (product.model or {}).get("properties", []) if product else []
            values = apply_property_formulas(props, values)
            merged.update(values)
        except Exception as exc:
            logger.warning("Thing formula: %s", exc)
        device.values = merged
        device.status = "online"
        device.last_online_at = datetime.utcnow()
        device.error = False
        device.error_string = None
        db.add(device)
        db.commit()
        db.refresh(device)

        try:
            from app.services.scene_engine import scene_engine
            scene_engine.on_device_values(db, device_id, values, merged)
        except Exception as exc:
            logger.warning("Scene engine: %s", exc)

        try:
            from app.crud.channel import shadow_crud
            shadow_crud.upsert_reported(db, device_id, values)
        except Exception as exc:
            logger.warning("Device shadow: %s", exc)

        try:
            from app.services.rule_engine import rule_engine
            rule_engine.on_values(db, device, values, merged, publish_alarm)
        except Exception as exc:
            logger.warning("Rule engine: %s", exc)

        try:
            from app.services.channel_runtime import channel_runtime
            channel_runtime.on_device_values(db, device, values)
        except Exception as exc:
            logger.warning("Channel runtime: %s", exc)

        try:
            from app.services.script_engine import script_engine
            script_engine.on_device_values(db, device_id, values, merged)
        except Exception as exc:
            logger.warning("Script engine: %s", exc)

        device_data_crud.create(
            db,
            DeviceDataCreate(
                device_id=device_id, data=values, data_type="property", quality="good"
            ),
        )

        validators = (product.model or {}).get("validators", []) if product else []
        for alarm_info in evaluate_validators(validators, merged):
            alarm = alarm_crud.create(
                db,
                AlarmCreate(
                    device_id=device.id,
                    product_id=device.product_id,
                    **alarm_info,
                ),
            )
            if publish_alarm:
                publish_alarm(device_id, {
                    "id": alarm.id,
                    "title": alarm.title,
                    "message": alarm.message,
                    "level": alarm.level,
                })
        return device

    def set_location(
        self, db: Session, device_id: str, lat: float, lng: float, geo_code: Optional[str] = None
    ) -> Optional[Device]:
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            return None
        device = device_crud.update(
            db,
            device,
            DeviceUpdate(latitude=lat, longitude=lng, geo_code=geo_code),
        )
        device_data_crud.create(
            db,
            DeviceDataCreate(
                device_id=device_id,
                data={"latitude": lat, "longitude": lng, "geo_code": geo_code},
                data_type="location",
                quality="good",
            ),
        )
        return device

    def set_error(self, db: Session, device_id: str, error_string: str) -> Optional[Device]:
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            return None
        device.error = True
        device.error_string = error_string
        db.add(device)
        db.commit()
        db.refresh(device)
        alarm_crud.create(
            db,
            AlarmCreate(
                device_id=device.id,
                product_id=device.product_id,
                title="设备故障",
                message=error_string,
                level="error",
                validator_name="error",
            ),
        )
        return device

    def _target_topic(self, device: Device, action: str) -> str:
        """有网关则发往网关主题"""
        if device.gateway_id:
            return f"device/{device.gateway_id}/{action}"
        return f"device/{device.device_id}/{action}"

    def request(
        self,
        mqtt_publish,
        device: Device,
        action: str,
        payload: Dict[str, Any],
        timeout: float = DEFAULT_TIMEOUT,
    ) -> Dict[str, Any]:
        """HTTP→MQTT 请求-响应，通过 msg_id 匹配"""
        msg_id = str(uuid.uuid4())
        body = {**payload, "msg_id": msg_id, "device_id": device.device_id}
        event = threading.Event()
        with _pending_lock:
            _pending[msg_id] = {"event": event, "response": None}

        topic = self._target_topic(device, action)
        mqtt_publish(topic, json.dumps(body))

        ok = event.wait(timeout)
        with _pending_lock:
            entry = _pending.pop(msg_id, None)
        if not ok or not entry:
            raise TimeoutError(f"设备响应超时({timeout}s): {action}")
        return entry.get("response") or {}

    def on_response(self, payload: Dict[str, Any]) -> None:
        """处理 */response 主题"""
        msg_id = payload.get("msg_id")
        if not msg_id:
            return
        with _pending_lock:
            entry = _pending.get(msg_id)
            if entry:
                entry["response"] = payload
                entry["event"].set()


device_runtime = DeviceRuntimeService()
