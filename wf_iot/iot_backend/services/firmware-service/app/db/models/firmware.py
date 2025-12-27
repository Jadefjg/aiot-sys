# 固件相关模型

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Firmware(Base):
    """固件表"""
    __tablename__ = "firmware"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(String(100), nullable=False, index=True)  # 适用于哪个产品线
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)  # 固件文件下载URL
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=True)  # 固件文件哈希值
    description = Column(Text, nullable=True)
    release_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_beta = Column(Boolean, default=False)
    min_hardware_version = Column(String(50), nullable=True)
    created_by = Column(Integer, nullable=True)  # 关联auth_db.users.id
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    upgrade_tasks = relationship("FirmwareUpgradeTask", back_populates="firmware", cascade="all, delete-orphan")


class FirmwareUpgradeTask(Base):
    """固件升级任务表"""
    __tablename__ = "firmware_upgrade_tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False, index=True)  # 关联device_db.devices.id
    device_identifier = Column(String(100), nullable=False, index=True)  # 冗余存储device_id字符串
    firmware_id = Column(Integer, ForeignKey("firmware.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)  # pending, in_progress, success, failed, cancelled
    progress = Column(Integer, default=0)  # 升级进度 (0-100)
    celery_task_id = Column(String(100), nullable=True, index=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    firmware = relationship("Firmware", back_populates="upgrade_tasks")
