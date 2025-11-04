"""
单元测试共享配置和 Fixtures
"""
import pytest
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_settings():
    """测试环境配置"""
    return {
        "SECRET_KEY": "test_secret_key_for_testing_only",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_device_data():
    """示例设备数据"""
    return {
        "device_id": "device001",
        "device_name": "Test Device",
        "product_id": "product001",
        "owner_id": 1
    }


@pytest.fixture
def sample_permission_data():
    """示例权限数据"""
    return {
        "name": "device:read",
        "description": "Read device information",
        "resource": "device",
        "action": "read"
    }


# 配置 pytest 标记
def pytest_configure(config):
    """配置自定义的 pytest 标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
