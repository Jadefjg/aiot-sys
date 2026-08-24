"""设备运行时：注册、属性、上下线、定位、故障（控制等待走 Redis）"""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.crud.alarm import alarm_crud
from app.crud.device import device_crud, device_data_crud
from app.crud.product import product_crud
from app.db.models.device import Device
from app.schemas.alarm import AlarmCreate
from app.schemas.device import DeviceCreate, DeviceDataCreate, DeviceUpdate
from app.services.validator_service import evaluate_validators

logger = logging.getLogger(__name__)


class DeviceRuntimeService:
    """设备生命周期中枢（落库在 device-service）"""

    def register(
        self,
        db: Session,
        device_id: str,
        product_id: Optional[str] = None,
        device_name: Optional[str] = None,
        gateway_id: Optional[str] = None,
    ) -> Device:
        device = device_crud.get_by_device_id(db, device_id)
        if device:
            device_crud.update_status(db, device_id, "online")
            return device_crud.get_by_device_id(db, device_id)

        pid = product_id or "default"
        product = product_crud.get_by_product_id(db, pid)
        name = device_name or (product.name if product else device_id)
        device_crud.create(
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
            children = db.query(Device).filter(Device.gateway_id == device_id).all()
            for child in children:
                child.status = "offline"
                db.add(child)
            db.commit()
        return device

    def put_values(
        self, db: Session, device_id: str, values: Dict[str, Any], publish_alarm=None
    ) -> Optional[Device]:
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            device = self.register(db, device_id)
        if device.disabled:
            return device

        merged = dict(device.values or {})
        merged.update(values)
        device.values = merged
        device.status = "online"
        device.last_online_at = datetime.utcnow()
        device.error = False
        device.error_string = None
        db.add(device)
        db.commit()
        db.refresh(device)

        device_data_crud.create(
            db,
            DeviceDataCreate(
                device_id=device_id, data=values, data_type="property", quality="good"
            ),
        )
        product = product_crud.get_by_product_id(db, device.product_id)
        validators = (product.model or {}).get("validators", []) if product else []
        for alarm_info in evaluate_validators(validators, merged):
            alarm = alarm_crud.create(
                db,
                AlarmCreate(device_id=device.id, product_id=device.product_id, **alarm_info),
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
        return device_crud.update(
            db, device, DeviceUpdate(latitude=lat, longitude=lng, geo_code=geo_code)
        )

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

    def target_topic(self, device: Device, action: str) -> str:
        if device.gateway_id:
            return f"device/{device.gateway_id}/{action}"
        return f"device/{device.device_id}/{action}"


device_runtime = DeviceRuntimeService()
