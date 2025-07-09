from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
# 导入所有模型以确保它们被注册到Base.metadata
from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.db.models.device import Device, DeviceData
from app.db.models.firmware import Firmware, FirmwareUpgradeTask