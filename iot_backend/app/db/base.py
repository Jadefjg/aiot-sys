from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# 导入所有模型以确保它们被注册到Base.metadata
# 这些导入必须在 Base 定义之后，以避免循环导入
def import_models():
    from app.db.models.user import User, Role, Permission, UserRole, RolePermission
    from app.db.models.device import Device, DeviceData
    from app.db.models.firmware import Firmware, FirmwareUpgradeTask
    return User, Role, Permission, UserRole, RolePermission, Device, DeviceData, Firmware, FirmwareUpgradeTask