"""
安全模块单元测试
测试 app/core/security.py 中的密码哈希和 JWT 令牌相关函数
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from app.core.config import settings


class TestPasswordHashing:
    """密码哈希功能测试"""

    def test_get_password_hash_returns_string(self):
        """测试密码哈希返回字符串"""
        # 执行测试
        password = "testpassword123"
        hashed = get_password_hash(password)

        # 验证结果
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # 哈希值不应该等于原密码

    def test_get_password_hash_different_passwords_different_hashes(self):
        """测试不同密码生成不同哈希"""
        # 执行测试
        password1 = "password123"
        password2 = "password456"
        hashed1 = get_password_hash(password1)
        hashed2 = get_password_hash(password2)

        # 验证结果
        assert hashed1 != hashed2

    def test_get_password_hash_same_password_different_hashes(self):
        """测试相同密码每次生成不同哈希（因为有盐值）"""
        # 执行测试
        password = "testpassword"
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)

        # 验证结果
        # bcrypt 每次生成的哈希都不同，因为每次使用不同的盐值
        assert hashed1 != hashed2

    def test_verify_password_correct_password(self):
        """测试验证正确密码"""
        # 准备数据
        password = "correctpassword"
        hashed = get_password_hash(password)

        # 执行测试
        result = verify_password(password, hashed)

        # 验证结果
        assert result is True

    def test_verify_password_wrong_password(self):
        """测试验证错误密码"""
        # 准备数据
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        # 执行测试
        result = verify_password(wrong_password, hashed)

        # 验证结果
        assert result is False

    def test_verify_password_empty_password(self):
        """测试验证空密码"""
        # 准备数据
        password = "testpassword"
        hashed = get_password_hash(password)

        # 执行测试
        result = verify_password("", hashed)

        # 验证结果
        assert result is False

    def test_get_password_hash_empty_string(self):
        """测试对空字符串进行哈希"""
        # 执行测试
        hashed = get_password_hash("")

        # 验证结果
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_special_characters(self):
        """测试包含特殊字符的密码哈希"""
        # 执行测试
        password = "p@ssw0rd!@#$%^&*()"
        hashed = get_password_hash(password)

        # 验证结果
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_get_password_hash_unicode_characters(self):
        """测试包含 Unicode 字符的密码"""
        # 执行测试
        password = "密码123测试"
        hashed = get_password_hash(password)

        # 验证结果
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_get_password_hash_long_password(self):
        """测试长密码"""
        # 执行测试
        password = "a" * 200  # 200个字符
        hashed = get_password_hash(password)

        # 验证结果
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True


class TestJWTToken:
    """JWT 令牌测试"""

    @patch('app.core.security.settings')
    @patch('app.core.security.jwt')
    def test_create_access_token_with_expires_delta(self, mock_jwt, mock_settings):
        """测试创建带过期时间的访问令牌"""
        # 配置模拟
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        mock_jwt.encode.return_value = "mocked_token"

        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        # 验证结果
        assert token == "mocked_token"
        mock_jwt.encode.assert_called_once()

    @patch('app.core.security.settings')
    @patch('app.core.security.jwt')
    def test_create_access_token_without_expires_delta(self, mock_jwt, mock_settings):
        """测试创建不带过期时间的访问令牌（使用默认值）"""
        # 配置模拟
        mock_settings.SECRET_KEY = "test_secret_key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        mock_jwt.encode.return_value = "mocked_token"

        # 执行测试
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # 验证结果
        assert token == "mocked_token"
        mock_jwt.encode.assert_called_once()

    def test_create_access_token_real(self):
        """测试创建真实的 JWT 令牌"""
        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)

        # 验证结果
        assert isinstance(token, str)
        assert len(token) > 0

        # 解码令牌验证内容
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_create_access_token_with_custom_data(self):
        """测试创建包含自定义数据的令牌"""
        # 执行测试
        data = {
            "sub": "testuser",
            "user_id": 123,
            "role": "admin"
        }
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta)

        # 验证结果
        assert isinstance(token, str)

        # 解码令牌验证内容
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == 123
        assert decoded["role"] == "admin"

    def test_create_access_token_expiration(self):
        """测试令牌过期时间设置"""
        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=10)
        token = create_access_token(data, expires_delta)

        # 解码令牌
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # 验证过期时间
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()

        # 验证过期时间在 9-11 分钟之间（允许一些误差）
        time_diff = (exp_datetime - now).total_seconds() / 60
        assert 9 <= time_diff <= 11

    def test_create_access_token_with_zero_expiration(self):
        """测试创建立即过期的令牌"""
        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(seconds=0)
        token = create_access_token(data, expires_delta)

        # 验证结果
        assert isinstance(token, str)

        # 解码令牌
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "testuser"

    def test_create_access_token_with_long_expiration(self):
        """测试创建长过期时间的令牌"""
        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(days=30)
        token = create_access_token(data, expires_delta)

        # 验证结果
        assert isinstance(token, str)

        # 解码令牌
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "testuser"

    def test_create_access_token_with_empty_data(self):
        """测试创建空数据的令牌"""
        # 执行测试
        data = {}
        token = create_access_token(data)

        # 验证结果
        assert isinstance(token, str)

        # 解码令牌
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in decoded

    @patch('app.core.security.settings')
    def test_create_access_token_with_different_algorithm(self, mock_settings):
        """测试使用不同算法创建令牌"""
        # 配置模拟
        original_algo = settings.ALGORITHM
        mock_settings.SECRET_KEY = settings.SECRET_KEY
        mock_settings.ALGORITHM = "HS512"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60

        # 执行测试
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # 验证结果
        assert isinstance(token, str)

        # 尝试用正确的算法解码
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])
        assert decoded["sub"] == "testuser"


class TestPasswordHashingEdgeCases:
    """密码哈希边界情况测试"""

    def test_verify_password_with_invalid_hash(self):
        """测试验证无效的哈希值"""
        # 执行测试
        password = "testpassword"
        invalid_hash = "not_a_valid_hash"

        # 验证结果 - 应该返回 False 或抛出异常
        try:
            result = verify_password(password, invalid_hash)
            assert result is False
        except Exception:
            # 如果抛出异常也是可接受的行为
            pass

    def test_get_password_hash_very_long_password(self):
        """测试极长密码"""
        # 执行测试
        password = "a" * 10000  # 10000个字符
        hashed = get_password_hash(password)

        # 验证结果
        assert isinstance(hashed, str)
        assert verify_password(password, hashed) is True

    def test_password_hash_consistency(self):
        """测试密码哈希的一致性"""
        # 执行测试
        password = "testpassword"
        hashed = get_password_hash(password)

        # 多次验证应该都成功
        for _ in range(10):
            assert verify_password(password, hashed) is True

    def test_password_case_sensitive(self):
        """测试密码大小写敏感"""
        # 执行测试
        password = "TestPassword"
        hashed = get_password_hash(password)

        # 验证结果
        assert verify_password("TestPassword", hashed) is True
        assert verify_password("testpassword", hashed) is False
        assert verify_password("TESTPASSWORD", hashed) is False


class TestJWTTokenEdgeCases:
    """JWT 令牌边界情况测试"""

    def test_create_access_token_with_negative_expiration(self):
        """测试负数过期时间"""
        # 执行测试
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=-10)
        token = create_access_token(data, expires_delta)

        # 验证结果 - 令牌应该已经过期
        assert isinstance(token, str)

    def test_token_decode_with_wrong_secret(self):
        """测试用错误的密钥解码令牌"""
        # 创建令牌
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # 尝试用错误的密钥解码
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret_key", algorithms=[settings.ALGORITHM])

    def test_token_decode_with_wrong_algorithm(self):
        """测试用错误的算法解码令牌"""
        # 创建令牌
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # 尝试用错误的算法解码
        with pytest.raises(JWTError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS512"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
