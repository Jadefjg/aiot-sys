# 固件CRUD操作

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from app.db.models.firmware import Firmware, FirmwareUpgradeTask
from app.schemas.firmware import (
    FirmwareCreate, FirmwareUpdate,
    FirmwareUpgradeTaskCreate, FirmwareUpgradeTaskUpdate
)


class CRUDFirmware:
    """固件CRUD操作"""

    def get(self, db: Session, firmware_id: int) -> Optional[Firmware]:
        """根据ID获取固件"""
        return db.query(Firmware).filter(Firmware.id == firmware_id).first()

    def get_by_version(self, db: Session, version: str) -> Optional[Firmware]:
        """根据版本号获取固件"""
        return db.query(Firmware).filter(Firmware.version == version).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Firmware], int]:
        """获取固件列表"""
        query = db.query(Firmware)
        if product_id:
            query = query.filter(Firmware.product_id == product_id)
        if is_active is not None:
            query = query.filter(Firmware.is_active == is_active)

        total = query.count()
        firmwares = query.order_by(desc(Firmware.created_at)).offset(skip).limit(limit).all()
        return firmwares, total

    def get_latest(self, db: Session, product_id: str, is_beta: bool = False) -> Optional[Firmware]:
        """获取指定产品的最新固件"""
        query = db.query(Firmware).filter(
            Firmware.product_id == product_id,
            Firmware.is_active == True
        )
        if not is_beta:
            query = query.filter(Firmware.is_beta == False)
        return query.order_by(desc(Firmware.created_at)).first()

    def create(self, db: Session, obj_in: FirmwareCreate, created_by: Optional[int] = None) -> Firmware:
        """创建固件"""
        db_obj = Firmware(
            **obj_in.model_dump(),
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Firmware, obj_in: FirmwareUpdate) -> Firmware:
        """更新固件"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, firmware_id: int) -> Optional[Firmware]:
        """删除固件"""
        obj = db.query(Firmware).filter(Firmware.id == firmware_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDUpgradeTask:
    """升级任务CRUD操作"""

    def get(self, db: Session, task_id: int) -> Optional[FirmwareUpgradeTask]:
        """根据ID获取任务"""
        return db.query(FirmwareUpgradeTask).filter(FirmwareUpgradeTask.id == task_id).first()

    def get_by_celery_id(self, db: Session, celery_task_id: str) -> Optional[FirmwareUpgradeTask]:
        """根据Celery任务ID获取任务"""
        return db.query(FirmwareUpgradeTask).filter(
            FirmwareUpgradeTask.celery_task_id == celery_task_id
        ).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        device_identifier: Optional[str] = None,
        status: Optional[str] = None
    ) -> tuple[List[FirmwareUpgradeTask], int]:
        """获取任务列表"""
        query = db.query(FirmwareUpgradeTask)
        if device_identifier:
            query = query.filter(FirmwareUpgradeTask.device_identifier == device_identifier)
        if status:
            query = query.filter(FirmwareUpgradeTask.status == status)

        total = query.count()
        tasks = query.order_by(desc(FirmwareUpgradeTask.created_at)).offset(skip).limit(limit).all()
        return tasks, total

    def create(self, db: Session, obj_in: FirmwareUpgradeTaskCreate, created_by: Optional[int] = None) -> FirmwareUpgradeTask:
        """创建升级任务"""
        db_obj = FirmwareUpgradeTask(
            **obj_in.model_dump(),
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: FirmwareUpgradeTask, obj_in: FirmwareUpgradeTaskUpdate) -> FirmwareUpgradeTask:
        """更新任务状态"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        if update_data.get("status") in ["success", "failed", "cancelled"]:
            db_obj.end_time = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def set_celery_task_id(self, db: Session, task_id: int, celery_task_id: str) -> Optional[FirmwareUpgradeTask]:
        """设置Celery任务ID"""
        task = self.get(db, task_id)
        if task:
            task.celery_task_id = celery_task_id
            task.status = "in_progress"
            db.add(task)
            db.commit()
            db.refresh(task)
        return task


# 实例化CRUD对象
firmware_crud = CRUDFirmware()
upgrade_task_crud = CRUDUpgradeTask()
