from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def import_models():
    """导入全部模型，确保 Base.metadata 完整"""
    from app.db.models.user import User, Role, Permission, UserRole, RolePermission
    from app.db.models.tenant import Tenant
    from app.db.models.group import DeviceGroup
    from app.db.models.device import Device, DeviceData, DeviceCommand
    from app.db.models.firmware import Firmware, FirmwareUpgradeTask, FirmwareRollout
    from app.db.models.product import Product
    from app.db.models.alarm import Alarm
    from app.db.models.smart import Scene, SceneExecution, Job, Binding, Script
    from app.db.models.link import Link
    from app.db.models.channel import Channel, ChannelLog, DataRule, DeviceShadow
    from app.db.models.acl import ProductACL, DeviceACL
    from app.db.models.media import DeviceMedia
    from app.db.models.agent_workflow import AgentWorkflow
    return (
        Tenant, User, Role, Permission, UserRole, RolePermission,
        DeviceGroup, Device, DeviceData, DeviceCommand,
        Firmware, FirmwareUpgradeTask, FirmwareRollout, Product, Alarm,
        Scene, SceneExecution, Job, Binding, Script, Link,
        Channel, ChannelLog, DataRule, DeviceShadow,
        ProductACL, DeviceACL, DeviceMedia, AgentWorkflow,
    )
