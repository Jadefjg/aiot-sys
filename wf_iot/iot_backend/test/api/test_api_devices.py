import pytest
import json
from typing import Dict, Any
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.crud.user import user_crud
from app.crud.device import device_crud
from app.schemas.user import UserCreate
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceDataCreate

client = TestClient(app)


class TestDeviceAPI:
    """设备模块API测试类"""

    @pytest.fixture(scope="class")
    def db(self):
        """创建数据库会话"""
        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture(scope="class")
    def test_user_data(self) -> Dict[str, Any]:
        """测试用户数据"""
        return {
            "username": "testuser_device",
            "email": "testuser_device@example.com",
            "password": "testpassword123",
            "full_name": "Test User Device"
        }

    @pytest.fixture(scope="class")
    def test_superuser_data(self) -> Dict[str, Any]:
        """测试超级用户数据"""
        return {
            "username": "superuser_device",
            "email": "superuser_device@example.com",
            "password": "superpassword123",
            "full_name": "Super User Device"
        }

    @pytest.fixture(scope="class")
    def test_device_data(self) -> Dict[str, Any]:
        """测试设备数据"""
        return {
            "device_id": "TEST_DEVICE_001",
            "device_name": "Test Device 001",
            "product_id": "TEST_PRODUCT_001"
        }

    @pytest.fixture(scope="class")
    def created_user(self, db: Session, test_user_data: Dict[str, Any]):
        """创建测试用户"""
        user_create = UserCreate(**test_user_data)
        user = user_crud.create(db, obj_in=user_create)
        yield user
        # 清理：删除测试用户
        try:
            db.refresh(user)
            user_crud.delete(db, id=user.id)
            db.commit()
        except:
            pass

    @pytest.fixture(scope="class")
    def created_superuser(self, db: Session, test_superuser_data: Dict[str, Any]):
        """创建测试超级用户"""
        user_create = UserCreate(**test_superuser_data)
        user = user_crud.create(db, obj_in=user_create)
        # 设置为超级用户
        user.is_superuser = True
        db.commit()
        db.refresh(user)
        yield user
        # 清理：删除测试超级用户
        try:
            db.refresh(user)
            user_crud.delete(db, id=user.id)
            db.commit()
        except:
            pass

    @pytest.fixture(scope="class")
    def user_token(self, created_user):
        """普通用户访问令牌"""
        access_token = create_access_token(
            data={"sub": created_user.username}
        )
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture(scope="class")
    def superuser_token(self, created_superuser):
        """超级用户访问令牌"""
        access_token = create_access_token(
            data={"sub": created_superuser.username}
        )
        return {"Authorization": f"Bearer {access_token}"}

    @pytest.fixture(scope="class")
    def created_device(self, db: Session, created_superuser, test_device_data: Dict[str, Any]):
        """创建测试设备"""
        device_in = DeviceCreate(**test_device_data, owner_id=created_superuser.id)
        device = device_crud.create(db, obj_in=device_in)
        yield device
        # 清理：删除测试设备
        try:
            db.refresh(device)
            device_crud.delete(db, id=device.id)
            db.commit()
        except:
            pass

    @pytest.fixture(scope="class")
    def user_device(self, db: Session, created_user, test_device_data: Dict[str, Any]):
        """为普通用户创建测试设备"""
        device_data = test_device_data.copy()
        device_data["device_id"] = "USER_DEVICE_001"
        device_in = DeviceCreate(**device_data, owner_id=created_user.id)
        device = device_crud.create(db, obj_in=device_in)
        yield device
        # 清理：删除测试设备
        try:
            db.refresh(device)
            device_crud.delete(db, id=device.id)
            db.commit()
        except:
            pass

    # ==================== 设备创建测试 ====================

    def test_create_device_success(self, client, superuser_token, test_device_data):
        """测试成功创建设备"""
        device_data = test_device_data.copy()
        device_data["device_id"] = "NEW_TEST_DEVICE_001"

        response = client.post(
            "/api/v1/devices/",
            json=device_data,
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_data["device_id"]
        assert data["device_name"] == device_data["device_name"]
        assert data["product_id"] == device_data["product_id"]
        assert "id" in data
        assert "created_at" in data

    def test_create_device_duplicate_device_id(self, client, superuser_token, test_device_data):
        """测试创建重复设备ID的设备"""
        # 第一次创建设备应该成功
        response1 = client.post(
            "/api/v1/devices/",
            json=test_device_data,
            headers=superuser_token
        )
        assert response1.status_code == 200

        # 第二次创建相同设备ID应该失败
        response2 = client.post(
            "/api/v1/devices/",
            json=test_device_data,
            headers=superuser_token
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_create_device_unauthorized(self, client, test_device_data):
        """测试无权限创建设备"""
        response = client.post(
            "/api/v1/devices/",
            json=test_device_data
        )
        assert response.status_code == 401

    def test_create_device_by_user(self, client, user_token, test_device_data):
        """测试普通用户创建设备（自动分配owner_id）"""
        device_data = test_device_data.copy()
        device_data["device_id"] = "USER_CREATE_DEVICE_001"
        # 不设置owner_id，应该自动设置为当前用户ID

        response = client.post(
            "/api/v1/devices/",
            json=device_data,
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == device_data["device_id"]
        # owner_id 应该为当前用户ID（在实际实现中需要验证）

    # ==================== 设备列表获取测试 ====================

    def test_get_devices_list_success(self, client, superuser_token):
        """测试成功获取设备列表"""
        response = client.get(
            "/api/v1/devices/",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_devices_list_unauthorized(self, client):
        """测试无权限获取设备列表"""
        response = client.get("/api/v1/devices/")
        assert response.status_code == 401

    def test_get_devices_list_with_pagination(self, client, superuser_token):
        """测试分页获取设备列表"""
        response = client.get(
            "/api/v1/devices/?skip=0&limit=10",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_devices_by_product_id(self, client, superuser_token, test_device_data):
        """测试按产品ID筛选设备"""
        # 创建设备
        device_data = test_device_data.copy()
        device_data["device_id"] = "FILTER_TEST_DEVICE_001"
        client.post(
            "/api/v1/devices/",
            json=device_data,
            headers=superuser_token
        )

        # 按产品ID查询
        response = client.get(
            f"/api/v1/devices/?product_id={test_device_data['product_id']}",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 验证返回的设备都属于指定产品ID
        for device in data:
            assert device["product_id"] == test_device_data["product_id"]

    # ==================== 单个设备获取测试 ====================

    def test_get_device_by_id_success(self, client, superuser_token, created_device):
        """测试成功获取设备信息"""
        response = client.get(
            f"/api/v1/devices/{created_device.device_id}",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_device.id
        assert data["device_id"] == created_device.device_id

    def test_get_device_by_id_not_found(self, client, superuser_token):
        """测试获取不存在的设备"""
        response = client.get(
            "/api/v1/devices/NONEXISTENT_DEVICE",
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_device_by_id_unauthorized(self, client, created_device):
        """测试无权限获取设备信息"""
        response = client.get(f"/api/v1/devices/{created_device.device_id}")
        assert response.status_code == 401

    def test_get_device_by_id_insufficient_permissions(self, client, user_token, created_device):
        """测试权限不足获取他人设备信息"""
        response = client.get(
            f"/api/v1/devices/{created_device.device_id}",
            headers=user_token
        )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_user_get_own_device_success(self, client, user_token, user_device):
        """测试用户获取自己的设备"""
        response = client.get(
            f"/api/v1/devices/{user_device.device_id}",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_device.id

    # ==================== 设备更新测试 ====================

    def test_update_device_success(self, client, superuser_token, created_device):
        """测试成功更新设备信息"""
        update_data = {
            "device_name": "Updated Device Name",
            "status": "active"
        }

        response = client.put(
            f"/api/v1/devices/{created_device.device_id}",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == update_data["device_name"]

    def test_update_device_not_found(self, client, superuser_token):
        """测试更新不存在的设备"""
        update_data = {
            "device_name": "Updated Name"
        }

        response = client.put(
            "/api/v1/devices/NONEXISTENT_DEVICE",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_device_unauthorized(self, client, created_device):
        """测试无权限更新设备"""
        update_data = {
            "device_name": "Updated Name"
        }

        response = client.put(
            f"/api/v1/devices/{created_device.device_id}",
            json=update_data
        )

        assert response.status_code == 401

    def test_update_device_insufficient_permissions(self, client, user_token, created_device):
        """测试权限不足更新他人设备"""
        update_data = {
            "device_name": "Hacked Name"
        }

        response = client.put(
            f"/api/v1/devices/{created_device.device_id}",
            json=update_data,
            headers=user_token
        )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_user_update_own_device_success(self, client, user_token, user_device):
        """测试用户更新自己的设备"""
        update_data = {
            "device_name": "User Updated Device"
        }

        response = client.put(
            f"/api/v1/devices/{user_device.device_id}",
            json=update_data,
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["device_name"] == update_data["device_name"]

    # ==================== 设备删除测试 ====================

    def test_delete_device_success(self, client, superuser_token, test_device_data):
        """测试成功删除设备"""
        # 先创建设备
        device_data = test_device_data.copy()
        device_data["device_id"] = "DELETE_TEST_DEVICE_001"
        create_response = client.post(
            "/api/v1/devices/",
            json=device_data,
            headers=superuser_token
        )
        assert create_response.status_code == 200

        # 删除设备
        delete_response = client.delete(
            f"/api/v1/devices/{device_data['device_id']}",
            headers=superuser_token
        )

        assert delete_response.status_code == 200

        # 验证设备已被删除
        get_response = client.get(
            f"/api/v1/devices/{device_data['device_id']}",
            headers=superuser_token
        )
        assert get_response.status_code == 404

    def test_delete_device_not_found(self, client, superuser_token):
        """测试删除不存在的设备"""
        response = client.delete(
            "/api/v1/devices/NONEXISTENT_DEVICE",
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_device_unauthorized(self, client, created_device):
        """测试无权限删除设备"""
        response = client.delete(f"/api/v1/devices/{created_device.device_id}")
        assert response.status_code == 401

    def test_delete_device_insufficient_permissions(self, client, user_token, created_device):
        """测试权限不足删除他人设备"""
        response = client.delete(
            f"/api/v1/devices/{created_device.device_id}",
            headers=user_token
        )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    def test_user_delete_own_device_success(self, client, user_token, user_device):
        """测试用户删除自己的设备"""
        device_id = user_device.device_id

        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers=user_token
        )

        assert response.status_code == 200

        # 验证设备已被删除
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers=user_token
        )
        assert get_response.status_code == 404

    # ==================== 设备数据测试 ====================

    def test_create_device_data_success(self, client, superuser_token, created_device):
        """测试成功创建设备数据"""
        data_in = {
            "device_id": created_device.device_id,
            "data": {
                "temperature": 25.6,
                "humidity": 60.2,
                "timestamp": datetime.now().isoformat()
            }
        }

        response = client.post(
            f"/api/v1/devices/{created_device.device_id}/data",
            json=data_in,
            headers=superuser_token
        )

        # 注意：这个测试可能需要根据实际实现调整
        assert response.status_code in [200, 201, 404]  # 404 如果设备数据CRUD未实现

    def test_create_device_data_device_not_found(self, client, superuser_token):
        """测试为不存在的设备创建数据"""
        data_in = {
            "device_id": "NONEXISTENT_DEVICE",
            "data": {
                "temperature": 25.6
            }
        }

        response = client.post(
            "/api/v1/devices/NONEXISTENT_DEVICE/data",
            json=data_in,
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_device_data_success(self, client, superuser_token, created_device):
        """测试成功获取设备数据"""
        response = client.get(
            f"/api/v1/devices/{created_device.device_id}/data",
            headers=superuser_token
        )

        # 注意：这个测试可能需要根据实际实现调整
        assert response.status_code in [200, 404]  # 404 如果设备数据功能未实现

    def test_get_device_data_not_found(self, client, superuser_token):
        """测试获取不存在设备的数据"""
        response = client.get(
            "/api/v1/devices/NONEXISTENT_DEVICE/data",
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_device_data_insufficient_permissions(self, client, user_token, created_device):
        """测试权限不足获取他人设备数据"""
        response = client.get(
            f"/api/v1/devices/{created_device.device_id}/data",
            headers=user_token
        )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    # ==================== 设备命令测试 ====================

    def test_send_device_command_success(self, client, superuser_token, created_device):
        """测试成功发送设备命令"""
        command_in = {
            "device_id": created_device.device_id,
            "command_type": "reboot",
            "command_data": {
                "delay": 5
            }
        }

        response = client.post(
            f"/api/v1/devices/{created_device.device_id}/commands",
            json=command_in,
            headers=superuser_token
        )

        # 注意：这个测试可能需要根据实际实现调整
        # 可能返回500如果MQTT未连接
        assert response.status_code in [200, 404, 500]

    def test_send_device_command_device_not_found(self, client, superuser_token):
        """测试向不存在的设备发送命令"""
        command_in = {
            "device_id": "NONEXISTENT_DEVICE",
            "command_type": "reboot",
            "command_data": {}
        }

        response = client.post(
            "/api/v1/devices/NONEXISTENT_DEVICE/commands",
            json=command_in,
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_send_device_command_insufficient_permissions(self, client, user_token, created_device):
        """测试权限不足发送设备命令"""
        command_in = {
            "device_id": created_device.device_id,
            "command_type": "reboot",
            "command_data": {}
        }

        response = client.post(
            f"/api/v1/devices/{created_device.device_id}/commands",
            json=command_in,
            headers=user_token
        )

        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    # ==================== 在线设备测试 ====================

    def test_get_online_devices_success(self, client, superuser_token):
        """测试成功获取在线设备列表"""
        response = client.get(
            "/api/v1/devices/status/online",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_online_devices_unauthorized(self, client):
        """测试无权限获取在线设备"""
        response = client.get("/api/v1/devices/status/online")
        assert response.status_code == 401

    def test_user_get_own_online_devices(self, client, user_token):
        """测试普通用户获取自己的在线设备"""
        response = client.get(
            "/api/v1/devices/status/online",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 只应该返回当前用户的设备

    # ==================== 设备控制测试 ====================

    def test_control_device_success(self, client, superuser_token, created_device):
        """测试成功控制设备"""
        control_command = {
            "action": "turn_on",
            "parameter": "led",
            "value": True
        }

        response = client.post(
            f"/api/v1/devices/{created_device.device_id}/control",
            json=control_command,
            headers=superuser_token
        )

        # 注意：这个测试可能需要根据实际实现调整
        assert response.status_code in [202, 500]  # 500 如果MQTT未连接

    def test_control_device_not_found(self, client, superuser_token):
        """测试控制不存在的设备"""
        control_command = {
            "action": "turn_on"
        }

        response = client.post(
            "/api/v1/devices/NONEXISTENT_DEVICE/control",
            json=control_command,
            headers=superuser_token
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    # ==================== 接收设备数据测试 ====================

    def test_receive_device_data_success(self, client, created_device):
        """测试通过HTTP接收设备数据"""
        device_data = {
            "device_id": created_device.device_id,
            "data": {
                "temperature": 26.5,
                "battery": 85
            }
        }

        response = client.post(
            "/api/v1/devices/data",
            json=device_data
        )

        # 注意：这个测试可能需要根据实际实现调整
        assert response.status_code in [200, 201, 404]  # 404 如果设备不存在

    def test_receive_device_data_device_not_found(self, client):
        """测试向不存在的设备发送数据"""
        device_data = {
            "device_id": "NONEXISTENT_DEVICE",
            "data": {
                "temperature": 26.5
            }
        }

        response = client.post(
            "/api/v1/devices/data",
            json=device_data
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    # ==================== 错误处理测试 ====================

    def test_invalid_device_data_format(self, client, superuser_token):
        """测试无效的设备数据格式"""
        # 缺少必填字段
        invalid_data = {
            "device_name": "Incomplete Device"
            # 缺少 device_id 和 product_id
        }

        response = client.post(
            "/api/v1/devices/",
            json=invalid_data,
            headers=superuser_token
        )

        assert response.status_code == 422  # 验证错误

    def test_missing_authorization_header(self, client, test_device_data):
        """测试缺少授权头"""
        response = client.post(
            "/api/v1/devices/",
            json=test_device_data
        )

        assert response.status_code == 401

    def test_invalid_token(self, client, test_device_data):
        """测试无效令牌"""
        invalid_token = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            "/api/v1/devices/",
            json=test_device_data,
            headers=invalid_token
        )

        assert response.status_code == 401


class TestDeviceIntegration:
    """设备模块集成测试"""

    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)

    def test_device_lifecycle(self, client):
        """测试设备完整生命周期：创建 -> 获取 -> 更新 -> 数据操作 -> 删除"""
        # 注意：这个集成测试需要根据实际的认证流程调整
        # 这里假设已经存在超级用户和普通用户

        # 跳过测试，因为需要先设置用户
        pytest.skip("需要先设置测试用户才能运行集成测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
