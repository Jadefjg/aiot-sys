"""
Pydantic Schemas 模块单元测试
测试 app/schemas/ 目录下的 Pydantic 模型
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.user import UserCreate, UserUpdate, User, RoleCreate, Role
from app.schemas.device import DeviceCreate, DeviceUpdate, Device, DeviceDataCreate
from app.schemas.permission import PermissionCreate, PermissionUpdate, Permission
from app.schemas.firmware import FirmwareCreate, Firmware, FirmwareUpgradeTaskCreate
from app.schemas.token import Token, TokenData


class TestUserSchemas:
    """用户相关 Schema 测试"""

    def test_user_create_valid(self):
        """测试创建有效的用户"""
        # 执行测试
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User",
            is_superuser=False
        )

        # 验证结果
        assert user_data.username == "testuser"
        assert user_data.email == "test@example.com"
        assert user_data.password == "password123"
        assert user_data.full_name == "Test User"
        assert user_data.is_superuser is False

    def test_user_create_invalid_email(self):
        """测试无效邮箱格式"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123"
            )

        # 验证错误信息
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("email",) for error in errors)

    def test_user_create_missing_required_fields(self):
        """测试缺少必填字段"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="testuser")

        # 验证错误信息
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_user_update_partial(self):
        """测试部分更新用户"""
        # 执行测试
        user_update = UserUpdate(full_name="Updated Name")

        # 验证结果
        assert user_update.full_name == "Updated Name"
        assert user_update.password is None
        assert user_update.email is None

    def test_user_update_all_fields(self):
        """测试更新所有字段"""
        # 执行测试
        user_update = UserUpdate(
            username="newusername",
            email="new@example.com",
            password="newpassword",
            full_name="New Name",
            is_active=False
        )

        # 验证结果
        assert user_update.username == "newusername"
        assert user_update.email == "new@example.com"
        assert user_update.password == "newpassword"
        assert user_update.full_name == "New Name"
        assert user_update.is_active is False

    def test_user_response_model(self):
        """测试用户响应模型"""
        # 执行测试
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        user = User(**user_data)

        # 验证结果
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_role_create_valid(self):
        """测试创建有效的角色"""
        # 执行测试
        role_data = RoleCreate(
            name="admin",
            description="Administrator role"
        )

        # 验证结果
        assert role_data.name == "admin"
        assert role_data.description == "Administrator role"

    def test_role_create_without_description(self):
        """测试创建不带描述的角色"""
        # 执行测试
        role_data = RoleCreate(name="editor")

        # 验证结果
        assert role_data.name == "editor"
        assert role_data.description is None


class TestDeviceSchemas:
    """设备相关 Schema 测试"""

    def test_device_create_valid(self):
        """测试创建有效的设备"""
        # 执行测试
        device_data = DeviceCreate(
            device_id="device001",
            device_name="Test Device",
            product_id="product001",
            owner_id=1
        )

        # 验证结果
        assert device_data.device_id == "device001"
        assert device_data.device_name == "Test Device"
        assert device_data.product_id == "product001"
        assert device_data.owner_id == 1

    def test_device_create_without_owner(self):
        """测试创建无所有者的设备"""
        # 执行测试
        device_data = DeviceCreate(
            device_id="device002",
            device_name="Test Device",
            product_id="product001"
        )

        # 验证结果
        assert device_data.owner_id is None

    def test_device_create_missing_required_fields(self):
        """测试缺少必填字段"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError):
            DeviceCreate(device_id="device001")

    def test_device_update_partial(self):
        """测试部分更新设备"""
        # 执行测试
        device_update = DeviceUpdate(device_name="Updated Device")

        # 验证结果
        assert device_update.device_name == "Updated Device"
        assert device_update.owner_id is None
        assert device_update.status is None

    def test_device_update_with_metadata(self):
        """测试更新设备元数据"""
        # 执行测试
        metadata = {"location": "Building A", "floor": 2}
        device_update = DeviceUpdate(metadata=metadata)

        # 验证结果
        assert device_update.metadata == metadata

    def test_device_data_create_valid(self):
        """测试创建有效的设备数据"""
        # 执行测试
        data = {"temperature": 25.5, "humidity": 60}
        device_data = DeviceDataCreate(
            device_id="device001",
            data=data
        )

        # 验证结果
        assert device_data.device_id == "device001"
        assert device_data.data == data

    def test_device_data_create_complex_data(self):
        """测试创建复杂数据结构"""
        # 执行测试
        data = {
            "sensors": {
                "temperature": 25.5,
                "humidity": 60,
                "pressure": 1013.25
            },
            "status": "active",
            "alerts": ["low_battery"]
        }
        device_data = DeviceDataCreate(
            device_id="device001",
            data=data
        )

        # 验证结果
        assert device_data.data == data
        assert device_data.data["sensors"]["temperature"] == 25.5


class TestPermissionSchemas:
    """权限相关 Schema 测试"""

    def test_permission_create_valid(self):
        """测试创建有效的权限"""
        # 执行测试
        permission_data = PermissionCreate(
            name="device:read",
            description="Read device information",
            resource="device",
            action="read"
        )

        # 验证结果
        assert permission_data.name == "device:read"
        assert permission_data.description == "Read device information"
        assert permission_data.resource == "device"
        assert permission_data.action == "read"

    def test_permission_create_without_description(self):
        """测试创建不带描述的权限"""
        # 执行测试
        permission_data = PermissionCreate(
            name="device:write",
            resource="device",
            action="write"
        )

        # 验证结果
        assert permission_data.name == "device:write"
        assert permission_data.description is None

    def test_permission_create_missing_required_fields(self):
        """测试缺少必填字段"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError):
            PermissionCreate(name="device:read")

    def test_permission_update_partial(self):
        """测试部分更新权限"""
        # 执行测试
        permission_update = PermissionUpdate(description="Updated description")

        # 验证结果
        assert permission_update.description == "Updated description"
        assert permission_update.name is None

    def test_permission_update_all_fields(self):
        """测试更新所有字段"""
        # 执行测试
        permission_update = PermissionUpdate(
            name="device:delete",
            description="Delete device",
            resource="device",
            action="delete"
        )

        # 验证结果
        assert permission_update.name == "device:delete"
        assert permission_update.description == "Delete device"

    def test_permission_response_model(self):
        """测试权限响应模型"""
        # 执行测试
        permission_data = {
            "id": 1,
            "name": "device:read",
            "description": "Read device",
            "resource": "device",
            "action": "read"
        }
        permission = Permission(**permission_data)

        # 验证结果
        assert permission.id == 1
        assert permission.name == "device:read"


class TestFirmwareSchemas:
    """固件相关 Schema 测试"""

    def test_firmware_create_valid(self):
        """测试创建有效的固件"""
        # 执行测试
        firmware_data = FirmwareCreate(
            version="1.0.0",
            product_id="product001",
            file_url="https://example.com/firmware.bin",
            file_hash="abc123",
            description="Firmware v1.0.0"
        )

        # 验证结果
        assert firmware_data.version == "1.0.0"
        assert firmware_data.product_id == "product001"
        assert str(firmware_data.file_url) == "https://example.com/firmware.bin"

    def test_firmware_create_without_optional_fields(self):
        """测试创建不带可选字段的固件"""
        # 执行测试
        firmware_data = FirmwareCreate(
            version="1.0.0",
            product_id="product001",
            file_url="https://example.com/firmware.bin"
        )

        # 验证结果
        assert firmware_data.file_hash is None
        assert firmware_data.description is None

    def test_firmware_create_invalid_url(self):
        """测试无效URL"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError):
            FirmwareCreate(
                version="1.0.0",
                product_id="product001",
                file_url="not-a-valid-url"
            )

    def test_firmware_upgrade_task_create_valid(self):
        """测试创建有效的固件升级任务"""
        # 执行测试
        task_data = FirmwareUpgradeTaskCreate(
            device_id=1,
            firmware_id=1
        )

        # 验证结果
        assert task_data.device_id == 1
        assert task_data.firmware_id == 1


class TestTokenSchemas:
    """令牌相关 Schema 测试"""

    def test_token_valid(self):
        """测试有效的令牌模型"""
        # 执行测试
        token_data = Token(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            token_type="bearer"
        )

        # 验证结果
        assert token_data.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        assert token_data.token_type == "bearer"

    def test_token_missing_fields(self):
        """测试缺少必填字段"""
        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError):
            Token(access_token="token123")

    def test_token_data_valid(self):
        """测试有效的令牌数据模型"""
        # 执行测试
        token_data = TokenData(username="testuser")

        # 验证结果
        assert token_data.username == "testuser"

    def test_token_data_none_username(self):
        """测试用户名为 None"""
        # 执行测试
        token_data = TokenData(username=None)

        # 验证结果
        assert token_data.username is None


class TestSchemasEdgeCases:
    """Schema 边界情况测试"""

    def test_user_create_empty_password(self):
        """测试空密码"""
        # 执行测试
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password=""
        )

        # 验证结果
        assert user_data.password == ""

    def test_user_create_very_long_username(self):
        """测试极长用户名"""
        # 执行测试
        long_username = "a" * 1000
        user_data = UserCreate(
            username=long_username,
            email="test@example.com",
            password="password123"
        )

        # 验证结果
        assert user_data.username == long_username

    def test_device_create_special_characters_in_id(self):
        """测试设备ID包含特殊字符"""
        # 执行测试
        device_data = DeviceCreate(
            device_id="device-001_test@#$",
            device_name="Test Device",
            product_id="product001"
        )

        # 验证结果
        assert device_data.device_id == "device-001_test@#$"

    def test_permission_create_colon_in_name(self):
        """测试权限名称包含冒号"""
        # 执行测试
        permission_data = PermissionCreate(
            name="resource:sub:action",
            resource="resource",
            action="action"
        )

        # 验证结果
        assert permission_data.name == "resource:sub:action"

    def test_device_data_empty_data_dict(self):
        """测试空数据字典"""
        # 执行测试
        device_data = DeviceDataCreate(
            device_id="device001",
            data={}
        )

        # 验证结果
        assert device_data.data == {}

    def test_user_update_no_fields(self):
        """测试不更新任何字段"""
        # 执行测试
        user_update = UserUpdate()

        # 验证结果
        assert user_update.username is None
        assert user_update.email is None
        assert user_update.password is None

    def test_firmware_version_formats(self):
        """测试各种版本号格式"""
        # 测试不同的版本号格式
        versions = ["1.0.0", "v1.0.0", "1.0", "1", "1.0.0-beta", "2.1.3-rc.1"]

        for version in versions:
            firmware_data = FirmwareCreate(
                version=version,
                product_id="product001",
                file_url="https://example.com/firmware.bin"
            )
            assert firmware_data.version == version


class TestSchemasSerialization:
    """Schema 序列化测试"""

    def test_user_model_dump(self):
        """测试用户模型序列化"""
        # 执行测试
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        dumped = user_data.model_dump()

        # 验证结果
        assert isinstance(dumped, dict)
        assert dumped["username"] == "testuser"
        assert dumped["email"] == "test@example.com"

    def test_device_model_dump_exclude_unset(self):
        """测试设备模型序列化（排除未设置的值）"""
        # 执行测试
        device_update = DeviceUpdate(device_name="Updated Device")
        dumped = device_update.model_dump(exclude_unset=True)

        # 验证结果
        assert "device_name" in dumped
        assert "owner_id" not in dumped
        assert "status" not in dumped

    def test_permission_model_dump_json(self):
        """测试权限模型 JSON 序列化"""
        # 执行测试
        permission_data = PermissionCreate(
            name="device:read",
            resource="device",
            action="read"
        )
        json_str = permission_data.model_dump_json()

        # 验证结果
        assert isinstance(json_str, str)
        assert "device:read" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
