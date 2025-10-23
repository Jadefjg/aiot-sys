import pytest
import json
from datetime import timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import SessionLocal
from app.crud.user import user_crud
from app.schemas.user import UserCreate


class TestAuthAPI:
    """认证模块API测试类"""
    
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
            "full_name": "Test User",
            "is_superuser": False
        }
    
    @pytest.fixture(scope="class")
    def inactive_user_data(self) -> Dict[str, Any]:
        """非活跃用户数据"""
        return {
            "username": "inactiveuser",
            "email": "inactive@example.com",
            "password": "password123",
            "full_name": "Inactive User",
            "is_superuser": False
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
    def created_inactive_user(self, db: Session, inactive_user_data: Dict[str, Any]):
        """创建非活跃测试用户"""
        user_create = UserCreate(**inactive_user_data)
        user = user_crud.create(db, obj_in=user_create)
        # 设置为非活跃状态
        user.is_active = False
        db.commit()
        db.refresh(user)
        yield user
        # 清理：删除测试用户
        try:
            user_crud.delete(db, id=user.id)
        except:
            pass
    
    def test_login_success(self, client, created_user, test_user_data):
        """测试成功登录"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_username(self, client, test_user_data):
        """测试无效用户名登录"""
        login_data = {
            "username": "nonexistentuser",
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, test_user_data):
        """测试无效密码登录"""
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, created_inactive_user, inactive_user_data):
        """测试非活跃用户登录"""
        login_data = {
            "username": inactive_user_data["username"],
            "password": inactive_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    def test_login_missing_username(self, client, test_user_data):
        """测试缺少用户名登录"""
        login_data = {
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 422  # 验证错误
    
    def test_login_missing_password(self, client, test_user_data):
        """测试缺少密码登录"""
        login_data = {
            "username": test_user_data["username"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 422  # 验证错误
    
    def test_login_empty_credentials(self, client):
        """测试空凭据登录"""
        login_data = {
            "username": "",
            "password": ""
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_test_token_success(self, client, created_user, test_user_data):
        """测试令牌验证成功"""
        # 首先获取令牌
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试令牌
        response = client.post("/api/v1/auth/test-token", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert data["id"] == created_user.id
    
    def test_test_token_invalid_token(self, client):
        """测试无效令牌"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post("/api/v1/auth/test-token", headers=headers)
        
        assert response.status_code == 401
    
    def test_test_token_missing_token(self, client):
        """测试缺少令牌"""
        response = client.post("/api/v1/auth/test-token")
        
        assert response.status_code == 401
    
    def test_test_token_expired_token(self, client, created_user, test_user_data):
        """测试过期令牌"""
        # 创建一个立即过期的令牌
        expired_token = create_access_token(
            data={"sub": test_user_data["username"]},
            expires_delta=timedelta(seconds=-1)  # 已过期
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.post("/api/v1/auth/test-token", headers=headers)
        
        assert response.status_code == 401
    
    def test_test_token_malformed_token(self, client):
        """测试格式错误的令牌"""
        headers = {"Authorization": "Bearer malformed.token.here"}
        
        response = client.post("/api/v1/auth/test-token", headers=headers)
        
        assert response.status_code == 401
    
    def test_login_with_email(self, client, created_user, test_user_data):
        """测试使用邮箱登录（如果支持的话）"""
        # 这个测试取决于系统是否支持邮箱登录
        # 如果支持，用户名和邮箱应该是等价的
        login_data = {
            "username": test_user_data["email"],  # 使用邮箱作为用户名
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        # 如果系统不支持邮箱登录，应该返回401
        # 如果支持，应该返回200
        # 这里假设不支持，所以期望401
        assert response.status_code == 401
    
    def test_token_contains_correct_claims(self, client, created_user, test_user_data):
        """测试令牌包含正确的声明"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        
        # 验证令牌格式（JWT令牌应该有三个部分，用.分隔）
        token_parts = token.split(".")
        assert len(token_parts) == 3
    
    def test_token_expiry_time(self, client, created_user, test_user_data):
        """测试令牌过期时间"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
        # 令牌应该包含过期信息
        # 这里我们只能验证令牌存在，具体的过期时间验证需要解析JWT
        token = response.json()["access_token"]
        assert token is not None
        assert len(token) > 0
    
    def test_login_case_sensitivity(self, client, created_user, test_user_data):
        """测试用户名大小写敏感性"""
        # 测试大写用户名
        login_data_upper = {
            "username": test_user_data["username"].upper(),
            "password": test_user_data["password"]
        }
        
        response_upper = client.post("/api/v1/auth/login", data=login_data_upper)
        
        # 测试小写用户名
        login_data_lower = {
            "username": test_user_data["username"].lower(),
            "password": test_user_data["password"]
        }
        
        response_lower = client.post("/api/v1/auth/login", data=login_data_lower)
        
        # 通常用户名应该是大小写敏感的
        # 如果大小写敏感，只有小写应该成功
        assert response_lower.status_code == 200
        # 如果系统是大小写敏感的，大写应该失败
        # 如果系统不是大小写敏感的，大写也应该成功
        # 这里假设系统是大小写敏感的
        assert response_upper.status_code == 401
    
    def test_password_case_sensitivity(self, client, created_user, test_user_data):
        """测试密码大小写敏感性"""
        # 测试大写密码
        login_data_upper = {
            "username": test_user_data["username"],
            "password": test_user_data["password"].upper()
        }
        
        response_upper = client.post("/api/v1/auth/login", data=login_data_upper)
        
        # 测试小写密码
        login_data_lower = {
            "username": test_user_data["username"],
            "password": test_user_data["password"].lower()
        }
        
        response_lower = client.post("/api/v1/auth/login", data=login_data_lower)
        
        # 密码应该是大小写敏感的
        assert response_upper.status_code == 401
        assert response_lower.status_code == 401  # 因为原始密码包含数字，小写版本也不对
    
    def test_login_rate_limiting(self, client, test_user_data):
        """测试登录频率限制（如果有的话）"""
        login_data = {
            "username": "nonexistentuser",
            "password": "wrongpassword"
        }
        
        # 尝试多次登录
        responses = []
        for i in range(5):
            response = client.post("/api/v1/auth/login", data=login_data)
            responses.append(response)
        
        # 如果没有频率限制，所有请求都应该返回401
        # 如果有频率限制，某些请求可能返回429（Too Many Requests）
        for response in responses:
            assert response.status_code in [401, 429]
    
    def test_concurrent_login_attempts(self, client, created_user, test_user_data):
        """测试并发登录尝试"""
        import threading
        import time
        
        results = []
        
        def login_attempt():
            login_data = {
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
            response = client.post("/api/v1/auth/login", data=login_data)
            results.append(response.status_code)
        
        # 创建多个线程同时登录
        threads = []
        for i in range(3):
            thread = threading.Thread(target=login_attempt)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 所有登录尝试都应该成功
        assert all(status == 200 for status in results)
        assert len(results) == 3


class TestAuthIntegration:
    """认证模块集成测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        return TestClient(app)
    
    def test_auth_flow(self, client):
        """测试完整的认证流程"""
        # 1. 创建一个测试用户（需要超级用户权限）
        # 这里假设已经存在超级用户
        superuser_login_data = {
            "username": "admin",  # 假设存在admin用户
            "password": "admin123"
        }
        
        # 尝试登录超级用户
        superuser_login_response = client.post("/api/v1/auth/login", data=superuser_login_data)
        if superuser_login_response.status_code != 200:
            pytest.skip("需要先创建超级用户才能运行集成测试")
        
        superuser_token = superuser_login_response.json()["access_token"]
        superuser_headers = {"Authorization": f"Bearer {superuser_token}"}
        
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
            headers=superuser_headers
        )
        if create_response.status_code != 200:
            pytest.skip("无法创建测试用户")
        
        # 3. 新用户登录
        user_login_data = {
            "username": new_user_data["username"],
            "password": new_user_data["password"]
        }
        
        user_login_response = client.post("/api/v1/auth/login", data=user_login_data)
        assert user_login_response.status_code == 200
        
        user_token = user_login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # 4. 验证令牌
        test_token_response = client.post("/api/v1/auth/test-token", headers=user_headers)
        assert test_token_response.status_code == 200
        
        user_info = test_token_response.json()
        assert user_info["username"] == new_user_data["username"]
        
        # 5. 使用令牌访问受保护的资源
        me_response = client.get("/api/v1/users/me", headers=user_headers)
        assert me_response.status_code == 200
        
        # 6. 测试令牌过期（如果有过期机制）
        # 这里可以添加更多集成测试逻辑


if __name__ == "__main__":
    pytest.main([__file__, "-v"])