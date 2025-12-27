# 设备CRUD操作

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta

from app.db.models.device import Device, DeviceData, DeviceCommand
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceDataCreate, DeviceCommandCreate


class CRUDDevice:
    """设备CRUD操作"""

    def get(self, db: Session, device_id: int) -> Optional[Device]:
        """根据ID获取设备"""
        return db.query(Device).filter(Device.id == device_id).first()

    def get_by_device_id(self, db: Session, device_id: str) -> Optional[Device]:
        """根据设备唯一标识获取设备"""
        return db.query(Device).filter(Device.device_id == device_id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[int] = None,
        status: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> tuple[List[Device], int]:
        """获取设备列表"""
        query = db.query(Device)
        if owner_id:
            query = query.filter(Device.owner_id == owner_id)
        if status:
            query = query.filter(Device.status == status)
        if product_id:
            query = query.filter(Device.product_id == product_id)

        total = query.count()
        devices = query.offset(skip).limit(limit).all()
        return devices, total

    def create(self, db: Session, obj_in: DeviceCreate) -> Device:
        """创建设备"""
        db_obj = Device(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Device, obj_in: DeviceUpdate) -> Device:
        """更新设备"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, device_id: int) -> Optional[Device]:
        """删除设备"""
        obj = db.query(Device).filter(Device.id == device_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def update_status(self, db: Session, device_id: str, status: str) -> Optional[Device]:
        """更新设备状态"""
        device = self.get_by_device_id(db, device_id)
        if device:
            device.status = status
            if status == "online":
                device.last_online_at = datetime.utcnow()
            db.add(device)
            db.commit()
            db.refresh(device)
        return device

    def batch_update_status(self, db: Session, device_ids: List[str], status: str) -> int:
        """批量更新设备状态"""
        update_data = {"status": status}
        if status == "online":
            update_data["last_online_at"] = datetime.utcnow()

        result = db.query(Device).filter(Device.device_id.in_(device_ids)).update(
            update_data, synchronize_session=False
        )
        db.commit()
        return result

    def get_online_devices(self, db: Session) -> List[Device]:
        """获取在线设备"""
        return db.query(Device).filter(Device.status == "online").all()


class CRUDDeviceData:
    """设备数据CRUD操作"""

    def create(self, db: Session, obj_in: DeviceDataCreate) -> Optional[DeviceData]:
        """创建设备数据"""
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

    def get_device_data(
        self,
        db: Session,
        device_id: int,
        data_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DeviceData]:
        """获取设备数据"""
        query = db.query(DeviceData).filter(DeviceData.device_id == device_id)
        if data_type:
            query = query.filter(DeviceData.data_type == data_type)
        if start_time:
            query = query.filter(DeviceData.timestamp >= start_time)
        if end_time:
            query = query.filter(DeviceData.timestamp <= end_time)
        return query.order_by(desc(DeviceData.timestamp)).limit(limit).all()

    def get_latest_data(self, db: Session, device_id: int, data_type: Optional[str] = None) -> Optional[DeviceData]:
        """获取最新设备数据"""
        query = db.query(DeviceData).filter(DeviceData.device_id == device_id)
        if data_type:
            query = query.filter(DeviceData.data_type == data_type)
        return query.order_by(desc(DeviceData.timestamp)).first()


class CRUDDeviceCommand:
    """设备命令CRUD操作"""

    def create(self, db: Session, obj_in: DeviceCommandCreate, created_by: Optional[int] = None) -> Optional[DeviceCommand]:
        """创建设备命令"""
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

    def update_status(
        self,
        db: Session,
        command_id: int,
        status: str,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Optional[DeviceCommand]:
        """更新命令状态"""
        command = db.query(DeviceCommand).filter(DeviceCommand.id == command_id).first()
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

    def get_device_commands(
        self,
        db: Session,
        device_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[DeviceCommand]:
        """获取设备命令列表"""
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            return []
        query = db.query(DeviceCommand).filter(DeviceCommand.device_id == device.id)
        if status:
            query = query.filter(DeviceCommand.status == status)
        return query.order_by(desc(DeviceCommand.created_at)).limit(limit).all()


# 实例化CRUD对象
device_crud = CRUDDevice()
device_data_crud = CRUDDeviceData()
device_command_crud = CRUDDeviceCommand()
