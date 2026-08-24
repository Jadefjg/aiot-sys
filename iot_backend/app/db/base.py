from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def import_models():
    """导入全部模型，确保 Base.metadata 完整"""
    from app.db.models.user import User, Role, Permission, UserRole, RolePermission
    from app.db.models.group import DeviceGroup
    from app.db.models.device import Device, DeviceData, DeviceCommand
    from app.db.models.firmware import Firmware, FirmwareUpgradeTask
    from app.db.models.product import Product
    from app.db.models.alarm import Alarm
    from app.db.models.smart import Scene, Job, Binding, Script
    return (
        User, Role, Permission, UserRole, RolePermission,
        DeviceGroup, Device, DeviceData, DeviceCommand,
        Firmware, FirmwareUpgradeTask, Product, Alarm,
        Scene, Job, Binding, Script,
    )