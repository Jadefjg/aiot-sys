import pytest
from datetime import timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.crud.user import user_crud
from app.crud.permission import permission_crud
from app.schemas.user import UserCreate
from app.schemas.permission import PermissionCreate


class TestPermissionAPI:
    """权限模块API测试类"""

    @pytest.fixture(scope="class")
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture(scope="class")
    def db(self):
        """创建数据库会话"""
        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture(scope="class")
    def test_user_data(self) -> Dict[str, Any]:
        """测试普通用户数据"""
        return {
            "username": "testuser_perm",
            "email": "testuser_perm@example.com",
            "password": "testpassword123",
            "full_name": "Test Permission User"
        }

    @pytest.fixture(scope="class")
    def test_superuser_data(self) -> Dict[str, Any]:
        """测试超级用户数据"""
        return {
            "username": "superuser_perm",
            "email": "superuser_perm@example.com",
            "password": "superpassword123",
            "full_name": "Super Permission User"
        }

    @pytest.fixture(scope="class")
    def created_user(self, db: Session, test_user_data: Dict[str, Any]):
        """创建测试普通用户"""
        user_create = UserCreate(**test_user_data)
        user = user_crud.create(db, obj_in=user_create)
        yield user
        # 清理：删除测试用户
        try:
            user_crud.delete(db, id=user.id)
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
            user_crud.delete(db, id=user.id)
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
    def test_permission_data(self) -> Dict[str, Any]:
        """测试权限数据"""
        return {
            "name": "device:read",
            "description": "Read device information",
            "resource": "device",
            "action": "read"
        }

    @pytest.fixture(scope="class")
    def created_permission(self, db: Session, test_permission_data: Dict[str, Any]):
        """创建测试权限"""
        permission_create = PermissionCreate(**test_permission_data)
        permission = permission_crud.create(db, obj_in=permission_create)
        yield permission
        # 清理：删除测试权限
        try:
            permission_crud.delete(db, permission_id=permission.id)
        except:
            pass

    # ========== 创建权限测试 ==========

    def test_create_permission_success(self, client, superuser_token):
        """测试成功创建权限"""
        permission_data = {
            "name": "user:create",
            "description": "Create new users",
            "resource": "user",
            "action": "create"
        }

        response = client.post(
            "/api/v1/permissions/",
            json=permission_data,
            headers=superuser_token
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == permission_data["name"]
        assert data["description"] == permission_data["description"]
        assert data["resource"] == permission_data["resource"]
        assert data["action"] == permission_data["action"]
        assert "id" in data

    def test_create_permission_duplicate_name(self, client, superuser_token, test_permission_data):
        """测试创建重复名称的权限"""
        response = client.post(
            "/api/v1/permissions/",
            json=test_permission_data,
            headers=superuser_token
        )

        assert response.status_code == 400
        assert "Permission with this name already exists" in response.json()["detail"]

    def test_create_permission_unauthorized(self, client, test_permission_data):
        """测试无权限创建权限"""
        response = client.post(
            "/api/v1/permissions/",
            json=test_permission_data
        )

        assert response.status_code == 401

    def test_create_permission_insufficient_permissions(self, client, user_token, test_permission_data):
        """测试权限不足创建权限"""
        permission_data = {
            "name": "user:update",
            "description": "Update users",
            "resource": "user",
            "action": "update"
        }

        response = client.post(
            "/api/v1/permissions/",
            json=permission_data,
            headers=user_token
        )

        assert response.status_code == 403

    def test_create_permission_missing_required_fields(self, client, superuser_token):
        """测试缺少必填字段"""
        incomplete_permission_data = {
            "name": "test:permission"
            # 缺少 resource 和 action 字段
        }

        response = client.post(
            "/api/v1/permissions/",
            json=incomplete_permission_data,
            headers=superuser_token
        )

        assert response.status_code == 422  # 验证错误

    # ========== 获取权限列表测试 ==========

    def test_get_permissions_list_success(self, client, user_token):
        """测试成功获取权限列表"""
        response = client.get(
            "/api/v1/permissions/",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_permissions_list_with_pagination(self, client, superuser_token):
        """测试分页获取权限列表"""
        response = client.get(
            "/api/v1/permissions/?skip=0&limit=10",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_get_permissions_list_unauthorized(self, client):
        """测试无权限获取权限列表"""
        response = client.get("/api/v1/permissions/")

        assert response.status_code == 401

    # ========== 获取单个权限测试 ==========

    def test_get_permission_by_id_success(self, client, user_token, created_permission):
        """测试成功根据ID获取权限"""
        response = client.get(
            f"/api/v1/permissions/{created_permission.id}",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_permission.id
        assert data["name"] == created_permission.name
        assert data["resource"] == created_permission.resource
        assert data["action"] == created_permission.action

    def test_get_permission_by_id_not_found(self, client, user_token):
        """测试获取不存在的权限"""
        response = client.get(
            "/api/v1/permissions/99999",
            headers=user_token
        )

        assert response.status_code == 404

    def test_get_permission_by_id_unauthorized(self, client, created_permission):
        """测试无权限根据ID获取权限"""
        response = client.get(f"/api/v1/permissions/{created_permission.id}")

        assert response.status_code == 401

    # ========== 根据资源类型获取权限测试 ==========

    def test_get_permissions_by_resource_success(self, client, user_token, created_permission):
        """测试成功根据资源类型获取权限"""
        response = client.get(
            f"/api/v1/permissions/resource/{created_permission.resource}",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 验证所有返回的权限都是指定的资源类型
        for permission in data:
            assert permission["resource"] == created_permission.resource

    def test_get_permissions_by_resource_empty(self, client, user_token):
        """测试根据不存在的资源类型获取权限"""
        response = client.get(
            "/api/v1/permissions/resource/nonexistent",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_permissions_by_resource_unauthorized(self, client):
        """测试无权限根据资源类型获取权限"""
        response = client.get("/api/v1/permissions/resource/device")

        assert response.status_code == 401

    # ========== 根据操作类型获取权限测试 ==========

    def test_get_permissions_by_action_success(self, client, user_token, created_permission):
        """测试成功根据操作类型获取权限"""
        response = client.get(
            f"/api/v1/permissions/action/{created_permission.action}",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 验证所有返回的权限都是指定的操作类型
        for permission in data:
            assert permission["action"] == created_permission.action

    def test_get_permissions_by_action_empty(self, client, user_token):
        """测试根据不存在的操作类型获取权限"""
        response = client.get(
            "/api/v1/permissions/action/nonexistent",
            headers=user_token
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_permissions_by_action_unauthorized(self, client):
        """测试无权限根据操作类型获取权限"""
        response = client.get("/api/v1/permissions/action/read")

        assert response.status_code == 401

    # ========== 更新权限测试 ==========

    def test_update_permission_success(self, client, superuser_token, created_permission):
        """测试成功更新权限"""
        update_data = {
            "description": "Updated permission description",
            "action": "write"
        }

        response = client.put(
            f"/api/v1/permissions/{created_permission.id}",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["action"] == update_data["action"]

    def test_update_permission_name(self, client, superuser_token, db, created_permission):
        """测试更新权限名称"""
        # 先创建一个新权限用于测试
        new_permission_data = {
            "name": "firmware:read",
            "description": "Read firmware",
            "resource": "firmware",
            "action": "read"
        }
        create_response = client.post(
            "/api/v1/permissions/",
            json=new_permission_data,
            headers=superuser_token
        )
        new_permission = create_response.json()

        # 更新名称
        update_data = {
            "name": "firmware:read_updated"
        }

        response = client.put(
            f"/api/v1/permissions/{new_permission['id']}",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]

        # 清理测试数据
        permission_crud.delete(db, permission_id=new_permission['id'])

    def test_update_permission_duplicate_name(self, client, superuser_token, db, created_permission):
        """测试更新权限为已存在的名称"""
        # 先创建第二个权限
        second_permission_data = {
            "name": "device:write",
            "description": "Write device",
            "resource": "device",
            "action": "write"
        }
        create_response = client.post(
            "/api/v1/permissions/",
            json=second_permission_data,
            headers=superuser_token
        )
        second_permission = create_response.json()

        # 尝试将第二个权限的名称更新为第一个权限的名称
        update_data = {
            "name": created_permission.name
        }

        response = client.put(
            f"/api/v1/permissions/{second_permission['id']}",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 400
        assert "Permission with this name already exists" in response.json()["detail"]

        # 清理测试数据
        permission_crud.delete(db, permission_id=second_permission['id'])

    def test_update_permission_not_found(self, client, superuser_token):
        """测试更新不存在的权限"""
        update_data = {
            "description": "Updated description"
        }

        response = client.put(
            "/api/v1/permissions/99999",
            json=update_data,
            headers=superuser_token
        )

        assert response.status_code == 404

    def test_update_permission_unauthorized(self, client, created_permission):
        """测试无权限更新权限"""
        update_data = {
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/permissions/{created_permission.id}",
            json=update_data
        )

        assert response.status_code == 401

    def test_update_permission_insufficient_permissions(self, client, user_token, created_permission):
        """测试权限不足更新权限"""
        update_data = {
            "description": "Updated description"
        }

        response = client.put(
            f"/api/v1/permissions/{created_permission.id}",
            json=update_data,
            headers=user_token
        )

        assert response.status_code == 403

    # ========== 删除权限测试 ==========

    def test_delete_permission_success(self, client, superuser_token, db):
        """测试成功删除权限"""
        # 先创建一个权限用于删除
        permission_data = {
            "name": "test:delete",
            "description": "Permission for delete test",
            "resource": "test",
            "action": "delete"
        }
        create_response = client.post(
            "/api/v1/permissions/",
            json=permission_data,
            headers=superuser_token
        )
        created = create_response.json()

        # 删除权限
        response = client.delete(
            f"/api/v1/permissions/{created['id']}",
            headers=superuser_token
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]

        # 验证权限已被删除
        get_response = client.get(
            f"/api/v1/permissions/{created['id']}",
            headers=superuser_token
        )
        assert get_response.status_code == 404

    def test_delete_permission_not_found(self, client, superuser_token):
        """测试删除不存在的权限"""
        response = client.delete(
            "/api/v1/permissions/99999",
            headers=superuser_token
        )

        assert response.status_code == 404

    def test_delete_permission_unauthorized(self, client, created_permission):
        """测试无权限删除权限"""
        response = client.delete(f"/api/v1/permissions/{created_permission.id}")

        assert response.status_code == 401

    def test_delete_permission_insufficient_permissions(self, client, user_token, created_permission):
        """测试权限不足删除权限"""
        response = client.delete(
            f"/api/v1/permissions/{created_permission.id}",
            headers=user_token
        )

        assert response.status_code == 403

    # ========== 令牌相关测试 ==========

    def test_invalid_token(self, client):
        """测试无效令牌"""
        invalid_token = {"Authorization": "Bearer invalid_token"}

        response = client.get(
            "/api/v1/permissions/",
            headers=invalid_token
        )

        assert response.status_code == 401

    def test_expired_token(self, client, test_user_data):
        """测试过期令牌"""
        # 创建一个立即过期的令牌
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get(
            "/api/v1/permissions/",
            headers=headers
        )

        assert response.status_code == 401


class TestPermissionIntegration:
    """权限模块集成测试"""

    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)

    @pytest.fixture(scope="class")
    def db(self):
        db = SessionLocal()
        yield db
        db.close()

    def test_permission_lifecycle(self, client, db):
        """测试权限完整生命周期：创建 -> 获取 -> 更新 -> 删除"""
        # 1. 创建超级用户
        superuser_data = {
            "username": "admin_perm_lifecycle",
            "email": "admin_perm_lifecycle@example.com",
            "password": "admin123",
            "full_name": "Administrator"
        }

        user_create = UserCreate(**superuser_data)
        superuser = user_crud.create(db, obj_in=user_create)
        superuser.is_superuser = True
        db.commit()
        db.refresh(superuser)

        # 获取超级用户令牌
        access_token = create_access_token(data={"sub": superuser.username})
        superuser_token = {"Authorization": f"Bearer {access_token}"}

        try:
            # 2. 创建权限
            permission_data = {
                "name": "lifecycle:test",
                "description": "Lifecycle test permission",
                "resource": "lifecycle",
                "action": "test"
            }

            create_response = client.post(
                "/api/v1/permissions/",
                json=permission_data,
                headers=superuser_token
            )
            assert create_response.status_code == 201
            created_permission = create_response.json()
            permission_id = created_permission["id"]

            # 3. 获取权限详情
            get_response = client.get(
                f"/api/v1/permissions/{permission_id}",
                headers=superuser_token
            )
            assert get_response.status_code == 200
            permission_info = get_response.json()
            assert permission_info["name"] == permission_data["name"]

            # 4. 更新权限
            update_data = {
                "description": "Updated lifecycle test permission",
                "action": "test_updated"
            }

            update_response = client.put(
                f"/api/v1/permissions/{permission_id}",
                json=update_data,
                headers=superuser_token
            )
            assert update_response.status_code == 200
            updated_permission = update_response.json()
            assert updated_permission["description"] == update_data["description"]
            assert updated_permission["action"] == update_data["action"]

            # 5. 验证更新
            get_updated_response = client.get(
                f"/api/v1/permissions/{permission_id}",
                headers=superuser_token
            )
            assert get_updated_response.status_code == 200
            final_permission_info = get_updated_response.json()
            assert final_permission_info["description"] == update_data["description"]

            # 6. 删除权限
            delete_response = client.delete(
                f"/api/v1/permissions/{permission_id}",
                headers=superuser_token
            )
            assert delete_response.status_code == 200

            # 7. 验证删除
            get_deleted_response = client.get(
                f"/api/v1/permissions/{permission_id}",
                headers=superuser_token
            )
            assert get_deleted_response.status_code == 404

        finally:
            # 清理：删除超级用户
            try:
                user_crud.delete(db, id=superuser.id)
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
