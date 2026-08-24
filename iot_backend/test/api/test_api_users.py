import pytest
import json
from datetime import timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.crud.user import user_crud
from app.schemas.user import UserCreate, UserUpdate


class TestUserAPI:
    """用户模块API测试类"""
    
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
        """测试用户数据"""
        return {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    
    @pytest.fixture(scope="class")
    def test_superuser_data(self) -> Dict[str, Any]:
        """测试超级用户数据"""
        return {
            "username": "superuser",
            "email": "superuser@example.com",
            "password": "superpassword123",
            "full_name": "Super User"
        }
    
    @pytest.fixture(scope="class")
    def created_user(self, db: Session, test_user_data: Dict[str, Any]):
        """创建测试用户"""
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
    
    def test_create_user_success(self, client, superuser_token, test_user_data):
        """测试成功创建用户"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=superuser_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_duplicate_username(self, client, superuser_token, test_user_data):
        """测试创建重复用户名的用户"""
        response = client.post(
            "/api/v1/users/",
            json=test_user_data,
            headers=superuser_token
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_create_user_duplicate_email(self, client, superuser_token, test_user_data):
        """测试创建重复邮箱的用户"""
        user_data = {
            "username": "anotheruser",
            "email": test_user_data["email"],  # 使用已存在的邮箱
            "password": "password123",
            "full_name": "Another User"
        }
        
        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers=superuser_token
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_create_user_unauthorized(self, client, test_user_data):
        """测试无权限创建用户"""
        response = client.post(
            "/api/v1/users/",
            json=test_user_data
        )
        
        assert response.status_code == 401
    
    def test_create_user_insufficient_permissions(self, client, user_token, test_user_data):
        """测试权限不足创建用户"""
        response = client.post(
            "/api/v1/users/",
            json=test_user_data,
            headers=user_token
        )
        
        assert response.status_code == 403
    
    def test_get_users_list_success(self, client, superuser_token):
        """测试成功获取用户列表"""
        response = client.get(
            "/api/v1/users/",
            headers=superuser_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_users_list_unauthorized(self, client):
        """测试无权限获取用户列表"""
        response = client.get("/api/v1/users/")
        
        assert response.status_code == 401
    
    def test_get_users_list_insufficient_permissions(self, client, user_token):
        """测试权限不足获取用户列表"""
        response = client.get(
            "/api/v1/users/",
            headers=user_token
        )
        
        assert response.status_code == 403
    
    def test_get_current_user_success(self, client, user_token, created_user):
        """测试成功获取当前用户信息"""
        response = client.get(
            "/api/v1/users/me",
            headers=user_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == created_user.username
        assert data["email"] == created_user.email
        assert data["id"] == created_user.id
    
    def test_get_current_user_unauthorized(self, client):
        """测试无权限获取当前用户信息"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
    
    def test_update_current_user_success(self, client, user_token, created_user):
        """测试成功更新当前用户信息"""
        update_data = {
            "full_name": "Updated Full Name",
            "email": "updated@example.com"
        }
        
        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=user_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
    
    def test_update_current_user_password(self, client, user_token):
        """测试更新当前用户密码"""
        update_data = {
            "password": "newpassword123"
        }
        
        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=user_token
        )
        
        assert response.status_code == 200
        # 密码不应该在响应中返回
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_update_current_user_unauthorized(self, client):
        """测试无权限更新当前用户信息"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(
            "/api/v1/users/me",
            json=update_data
        )
        
        assert response.status_code == 401
    
    def test_get_user_by_id_success(self, client, superuser_token, created_user):
        """测试成功根据ID获取用户信息"""
        response = client.get(
            f"/api/v1/users/{created_user.id}",
            headers=superuser_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user.id
        assert data["username"] == created_user.username
    
    def test_get_user_by_id_self_access(self, client, user_token, created_user):
        """测试用户获取自己的信息"""
        response = client.get(
            f"/api/v1/users/{created_user.id}",
            headers=user_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user.id
    
    def test_get_user_by_id_unauthorized(self, client, created_user):
        """测试无权限根据ID获取用户信息"""
        response = client.get(f"/api/v1/users/{created_user.id}")
        
        assert response.status_code == 401
    
    def test_get_user_by_id_not_found(self, client, superuser_token):
        """测试获取不存在的用户信息"""
        response = client.get(
            "/api/v1/users/99999",
            headers=superuser_token
        )
        
        assert response.status_code == 404
    
    def test_get_user_by_id_insufficient_permissions(self, client, user_token, created_superuser):
        """测试权限不足获取其他用户信息"""
        response = client.get(
            f"/api/v1/users/{created_superuser.id}",
            headers=user_token
        )
        
        assert response.status_code == 404  # 返回404而不是403，保护用户隐私
    
    def test_update_user_success(self, client, superuser_token, created_user):
        """测试成功更新指定用户信息"""
        update_data = {
            "full_name": "Updated User Name",
            "email": "updateduser@example.com"
        }
        
        response = client.put(
            f"/api/v1/users/{created_user.id}",
            json=update_data,
            headers=superuser_token
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
    
    def test_update_user_not_found(self, client, superuser_token):
        """测试更新不存在的用户"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(
            "/api/v1/users/99999",
            json=update_data,
            headers=superuser_token
        )
        
        assert response.status_code == 404
    
    def test_update_user_unauthorized(self, client, created_user):
        """测试无权限更新用户信息"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(
            f"/api/v1/users/{created_user.id}",
            json=update_data
        )
        
        assert response.status_code == 401
    
    def test_invalid_token(self, client, test_user_data):
        """测试无效令牌"""
        invalid_token = {"Authorization": "Bearer invalid_token"}
        
        response = client.get(
            "/api/v1/users/me",
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
            "/api/v1/users/me",
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_user_validation_errors(self, client, superuser_token):
        """测试用户数据验证错误"""
        # 测试无效邮箱格式
        invalid_user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Test User"
        }
        
        response = client.post(
            "/api/v1/users/",
            json=invalid_user_data,
            headers=superuser_token
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_missing_required_fields(self, client, superuser_token):
        """测试缺少必填字段"""
        incomplete_user_data = {
            "username": "testuser"
            # 缺少密码和其他必填字段
        }
        
        response = client.post(
            "/api/v1/users/",
            json=incomplete_user_data,
            headers=superuser_token
        )
        
        assert response.status_code == 422  # 验证错误


class TestUserIntegration:
    """用户模块集成测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    def test_user_lifecycle(self, client):
        """测试用户完整生命周期：注册 -> 登录 -> 获取信息 -> 更新 -> 删除"""
        # 1. 创建超级用户（用于管理其他用户）
        superuser_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password": "admin123",
            "full_name": "Administrator"
        }
        
        # 这里需要先通过某种方式创建超级用户，或者使用现有的
        # 假设已经存在超级用户，获取令牌
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        if login_response.status_code != 200:
            pytest.skip("需要先创建超级用户才能运行集成测试")
        
        superuser_token = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }
        
        # 2. 创建新用户
        new_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        create_response = client.post(
            "/api/v1/users/",
            json=new_user_data,
            headers=superuser_token
        )
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # 3. 新用户登录
        user_login_data = {
            "username": new_user_data["username"],
            "password": new_user_data["password"]
        }
        
        user_login_response = client.post("/api/v1/auth/login", data=user_login_data)
        assert user_login_response.status_code == 200
        user_token = {
            "Authorization": f"Bearer {user_login_response.json()['access_token']}"
        }
        
        # 4. 获取用户信息
        me_response = client.get("/api/v1/users/me", headers=user_token)
        assert me_response.status_code == 200
        user_info = me_response.json()
        assert user_info["username"] == new_user_data["username"]
        
        # 5. 更新用户信息
        update_data = {
            "full_name": "Updated User Name",
            "email": "updated@example.com"
        }
        
        update_response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers=user_token
        )
        assert update_response.status_code == 200
        updated_user = update_response.json()
        assert updated_user["full_name"] == update_data["full_name"]
        assert updated_user["email"] == update_data["email"]
        
        # 6. 验证更新
        me_response_after_update = client.get("/api/v1/users/me", headers=user_token)
        assert me_response_after_update.status_code == 200
        final_user_info = me_response_after_update.json()
        assert final_user_info["full_name"] == update_data["full_name"]
        assert final_user_info["email"] == update_data["email"]
        
        # 7. 清理：删除测试用户（通过超级用户）
        # 注意：实际的删除功能需要在API中实现
        # delete_response = client.delete(f"/api/v1/users/{created_user['id']}", headers=superuser_token)
        # assert delete_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
