from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from app.db.models.device import Device, DeviceData, DeviceCommand
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceDataCreate,DeviceCommandCreate


class CRUDDevice:
    def get(self, db: Session, id: int) -> Optional[Device]:
        return db.query(Device).filter(Device.id == id).first()

    def get_by_device_id(self, db: Session, device_id: str) -> Optional[Device]:
        return db.query(Device).filter(Device.device_id == device_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100, owner_id:
        Optional[int] = None) -> List[Device]:
        query = db.query(Device)
        if owner_id:
            query = query.filter(Device.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    def get_by_product(self, db: Session, product_id: str, skip: int = 0,limit: int = 100) -> List[Device]:
        return db.query(Device).filter(Device.product_id == product_id).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: DeviceCreate) -> Device:
        db_obj = Device(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Device, obj_in: DeviceUpdate) -> Device:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Device:
        obj = db.query(Device).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def update_status(self, db: Session, device_id: str, status: str) -> Optional[Device]:
        device = self.get_by_device_id(db, device_id)
        if device:
            device.status = status
        if status == "online":
            device.last_online_at = datetime.utcnow()
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    def get_online_devices(self, db: Session) -> List[Device]:
        return db.query(Device).filter(Device.status == "online").all()

    def get_offline_devices(self, db: Session, minutes: int = 30) -> List[Device]:
        """获取超过指定分钟数未上线的设备"""
        threshold = datetime.utcnow() - timedelta(minutes=minutes)
        return db.query(Device).filter(
            and_(
            Device.status == "offline",
            Device.last_online_at < threshold
            )
          ).all()


class CRUDDeviceData:
    def create(self, db: Session, obj_in: DeviceDataCreate) -> Optional[DeviceData]:
        # 首先获取设备
        device = device_crud.get_by_device_id(db, obj_in.device_id)
        if not device:
            return None
        db_obj = DeviceData(
        device_id=device.id,
        data_type=obj_in.data_type,
        data=obj_in.data,
        quality=obj_in.quality
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_device_data(self, db: Session, device_id: int, skip: int = 0,limit: int = 100) -> List[DeviceData]:
        return db.query(DeviceData).filter(DeviceData.device_id == device_id).order_by(
            desc(DeviceData.timestamp)
            ).offset(skip).limit(limit).all()

    def get_latest_data(self, db: Session, device_id: int) -> Optional[DeviceData]:
        return db.query(DeviceData).filter(DeviceData.device_id == device_id).order_by(desc(DeviceData.timestamp)).first()

    def get_data_by_time_range(self, db: Session, device_id: int, start_time:datetime, end_time: datetime) -> List[DeviceData]:
        return db.query(DeviceData).filter(and_(DeviceData.device_id == device_id,DeviceData.timestamp >= start_time,DeviceData.timestamp <= end_time)).order_by(DeviceData.timestamp).all()


class CRUDDeviceCommand:
    def create(self, db: Session, obj_in: DeviceCommandCreate, created_by: int) -> Optional[DeviceCommand]:
        device = device_crud.get_by_device_id(db, obj_in.device_id)
        if not device:
            return None
        db_obj = DeviceCommand(
            device_id=device.id,
            command_type=obj_in.command_type,
            command_data=obj_in.command_data,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(self, db: Session, command_id: int, status: str,response_data: Optional[Dict[str, Any]] = None) -> Optional[DeviceCommand]:
        command = db.query(DeviceCommand).get(command_id)
        if command:
            command.status = status
        if status == "sent":
            command.sent_at = datetime.utcnow()
        elif status == "acknowledged":
            command.acknowledged_at = datetime.utcnow()
        if response_data:
            command.response_data = response_data
            db.add(command)
            db.commit()
            db.refresh(command)
        return command

    def get_pending_commands(self, db: Session, device_id: str) -> List[DeviceCommand]:
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            return []
        return db.query(DeviceCommand).filter(
            and_(
            DeviceCommand.device_id == device.id,
            DeviceCommand.status == "pending"
            )
        ).all()


# 实例化CRUD对象
device_crud = CRUDDevice()
device_data_crud = CRUDDeviceData()
device_command_crud = CRUDDeviceCommand()