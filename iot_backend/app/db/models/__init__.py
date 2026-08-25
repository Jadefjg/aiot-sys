"""导出全部 ORM 模型"""
from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.db.models.group import DeviceGroup
from app.db.models.device import Device, DeviceData, DeviceCommand
from app.db.models.firmware import Firmware, FirmwareUpgradeTask
from app.db.models.product import Product
from app.db.models.alarm import Alarm
from app.db.models.smart import Scene, Job, Binding, Script
from app.db.models.link import Link
from app.db.models.channel import Channel, ChannelLog, DataRule, DeviceShadow
from app.db.models.acl import ProductACL, DeviceACL

__all__ = [
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "DeviceGroup", "Device", "DeviceData", "DeviceCommand",
    "Firmware", "FirmwareUpgradeTask", "Product", "Alarm",
    "Scene", "Job", "Binding", "Script", "Link",
    "Channel", "ChannelLog", "DataRule", "DeviceShadow",
    "ProductACL", "DeviceACL",
]
