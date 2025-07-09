from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Firmware(Base):
    __tablename__ = "firmware"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False)
    product_id = Column(String(100), nullable=False)  # 适用于哪个产品线
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)  # 固件文件下载URL
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=True)  # 固件文件哈希值，用于校验
    description = Column(Text, nullable=True)
    release_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=True)
    is_beta = Column(Boolean, nullable=True)
    min_harware_version = Column(String(50), nullable=True)
    create_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    creator = relationship("User", foreign_keys=[create_by])
    upgrade_tasks = relationship("FirmwareUpgradeTask", back_populates="upgrade_task")

    # 唯一约束
    __table_args__ = (
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )


class FirmwareUpgradeTask(Base):
    __tablename__ = "firmware_upgrade_tasks"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)  # 目标设备
    firmware_id = Column(Integer, ForeignKey("firmwares.id"), nullable=False)  #目标固件
    status = Column(String(20), default="pending")  # pending, in_progress,success, failed, cancelled
    progress = Column(Integer, default=0)  # 升级进度 (0-100)
    celery_task_id = Column(String(100), nullable=True, index=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,onupdate=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="upgrade_tasks")
    firmware = relationship("Firmware", back_populates="upgrade_tasks")
    creator = relationship("User")
