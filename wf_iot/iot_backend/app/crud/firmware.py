"""
固件管理CRUD操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime

from app.db.models.firmware import Firmware, FirmwareUpgradeTask
from app.schemas.firmware import FirmwareCreate, FirmwareUpgradeTaskCreate


class CRUDFirmware:
    """固件CRUD操作类"""

    def get(self, db: Session, id: int) -> Optional[Firmware]:
        """根据ID获取固件"""
        return db.query(Firmware).filter(Firmware.id == id).first()

    def get_by_version(self, db: Session, version: str) -> Optional[Firmware]:
        """根据版本号获取固件"""
        return db.query(Firmware).filter(Firmware.version == version).first()

    def get_by_version_and_product(
        self, db: Session, version: str, product_id: str
    ) -> Optional[Firmware]:
        """根据版本号和产品ID获取固件"""
        return db.query(Firmware).filter(
            and_(Firmware.version == version, Firmware.product_id == product_id)
        ).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, product_id: Optional[str] = None
    ) -> List[Firmware]:
        """获取固件列表"""
        query = db.query(Firmware)
        if product_id:
            query = query.filter(Firmware.product_id == product_id)
        return query.order_by(desc(Firmware.created_at)).offset(skip).limit(limit).all()

    def get_active_firmware(self, db: Session, product_id: str) -> List[Firmware]:
        """获取产品的活跃固件"""
        return db.query(Firmware).filter(
            and_(Firmware.product_id == product_id, Firmware.is_active == True)
        ).order_by(desc(Firmware.created_at)).all()

    def get_latest_firmware(self, db: Session, product_id: str) -> Optional[Firmware]:
        """获取产品的最新固件"""
        return db.query(Firmware).filter(
            and_(Firmware.product_id == product_id, Firmware.is_active == True)
        ).order_by(desc(Firmware.created_at)).first()

    def create(
        self, db: Session, obj_in: FirmwareCreate, created_by: Optional[int] = None,
        file_name: str = "", file_path: str = "", file_size: int = 0
    ) -> Firmware:
        """创建固件"""
        db_obj = Firmware(
            version=obj_in.version,
            product_id=obj_in.product_id,
            file_url=str(obj_in.file_url),
            file_hash=obj_in.file_hash,
            description=obj_in.description,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            is_active=True,
            is_beta=False,
            create_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: Firmware,
        version: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_beta: Optional[bool] = None,
        release_notes: Optional[str] = None
    ) -> Firmware:
        """更新固件信息"""
        if version is not None:
            db_obj.version = version
        if description is not None:
            db_obj.description = description
        if is_active is not None:
            db_obj.is_active = is_active
        if is_beta is not None:
            db_obj.is_beta = is_beta
        if release_notes is not None:
            db_obj.release_notes = release_notes
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Firmware]:
        """删除固件"""
        obj = db.query(Firmware).filter(Firmware.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def set_active(self, db: Session, id: int, is_active: bool) -> Optional[Firmware]:
        """设置固件激活状态"""
        obj = self.get(db, id)
        if obj:
            obj.is_active = is_active
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj


class CRUDFirmwareUpgradeTask:
    """固件升级任务CRUD操作类"""

    def get(self, db: Session, id: int) -> Optional[FirmwareUpgradeTask]:
        """根据ID获取升级任务"""
        return db.query(FirmwareUpgradeTask).filter(FirmwareUpgradeTask.id == id).first()

    def get_by_celery_task_id(self, db: Session, celery_task_id: str) -> Optional[FirmwareUpgradeTask]:
        """根据Celery任务ID获取升级任务"""
        return db.query(FirmwareUpgradeTask).filter(
            FirmwareUpgradeTask.celery_task_id == celery_task_id
        ).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100,
        device_id: Optional[int] = None, status: Optional[str] = None
    ) -> List[FirmwareUpgradeTask]:
        """获取升级任务列表"""
        query = db.query(FirmwareUpgradeTask)
        if device_id:
            query = query.filter(FirmwareUpgradeTask.device_id == device_id)
        if status:
            query = query.filter(FirmwareUpgradeTask.status == status)
        return query.order_by(desc(FirmwareUpgradeTask.created_at)).offset(skip).limit(limit).all()

    def get_device_tasks(self, db: Session, device_id: int) -> List[FirmwareUpgradeTask]:
        """获取设备的所有升级任务"""
        return db.query(FirmwareUpgradeTask).filter(
            FirmwareUpgradeTask.device_id == device_id
        ).order_by(desc(FirmwareUpgradeTask.created_at)).all()

    def get_pending_tasks(self, db: Session) -> List[FirmwareUpgradeTask]:
        """获取所有待处理的升级任务"""
        return db.query(FirmwareUpgradeTask).filter(
            FirmwareUpgradeTask.status == "pending"
        ).all()

    def create(
        self, db: Session, obj_in: FirmwareUpgradeTaskCreate, created_by: Optional[int] = None
    ) -> FirmwareUpgradeTask:
        """创建升级任务"""
        db_obj = FirmwareUpgradeTask(
            device_id=obj_in.device_id,
            firmware_id=obj_in.firmware_id,
            status="pending",
            progress=0,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(
        self, db: Session, id: int, status: str,
        progress: Optional[int] = None, error_message: Optional[str] = None
    ) -> Optional[FirmwareUpgradeTask]:
        """更新升级任务状态"""
        task = self.get(db, id)
        if task:
            task.status = status
            if progress is not None:
                task.progress = progress
            if error_message:
                task.error_message = error_message
            if status in ["success", "failed", "cancelled"]:
                task.end_time = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)
        return task

    def update_celery_task_id(
        self, db: Session, id: int, celery_task_id: str
    ) -> Optional[FirmwareUpgradeTask]:
        """更新Celery任务ID"""
        task = self.get(db, id)
        if task:
            task.celery_task_id = celery_task_id
            db.add(task)
            db.commit()
            db.refresh(task)
        return task

    def update_progress(self, db: Session, id: int, progress: int) -> Optional[FirmwareUpgradeTask]:
        """更新升级进度"""
        task = self.get(db, id)
        if task:
            task.progress = progress
            if progress >= 100:
                task.status = "success"
                task.end_time = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)
        return task

    def cancel_task(self, db: Session, id: int) -> Optional[FirmwareUpgradeTask]:
        """取消升级任务"""
        return self.update_status(db, id, "cancelled")

    def delete(self, db: Session, id: int) -> Optional[FirmwareUpgradeTask]:
        """删除升级任务"""
        obj = db.query(FirmwareUpgradeTask).filter(FirmwareUpgradeTask.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# 实例化CRUD对象
firmware_crud = CRUDFirmware()
firmware_upgrade_task_crud = CRUDFirmwareUpgradeTask()
