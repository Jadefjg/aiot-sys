"""产品 / 设备级 ACL：viewer < operator < admin"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.db.base import Base


class ProductACL(Base):
    """用户对产品的授权"""

    __tablename__ = "product_acls"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_product_acl"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)


class DeviceACL(Base):
    """用户对单台设备的授权（覆盖产品级角色）"""

    __tablename__ = "device_acls"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_device_acl"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)
