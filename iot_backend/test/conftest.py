import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.db.base import Base
from app.crud.user import user_crud
from app.schemas.user import UserCreate


# 创建测试数据库引擎
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """创建测试数据库引擎"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    yield engine
    # 清理：删除所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """创建数据库会话"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data() -> Dict[str, Any]:
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "is_superuser": False
    }


@pytest.fixture(scope="function")
def test_superuser_data() -> Dict[str, Any]:
    """测试超级用户数据"""
    return {
        "username": "superuser",
        "email": "superuser@example.com",
        "password": "superpassword123",
        "full_name": "Super User",
        "is_superuser": True
    }


@pytest.fixture(scope="function")
def created_user(db: Session, test_user_data: Dict[str, Any]):
    """创建测试用户"""
    user_create = UserCreate(**test_user_data)
    user = user_crud.create(db, obj_in=user_create)
    yield user
    # 清理在db fixture中自动处理


@pytest.fixture(scope="function")
def created_superuser(db: Session, test_superuser_data: Dict[str, Any]):
    """创建测试超级用户"""
    user_create = UserCreate(**test_superuser_data)
    user = user_crud.create(db, obj_in=user_create)
    yield user
    # 清理在db fixture中自动处理


@pytest.fixture(scope="function")
def user_token(created_user):
    """普通用户访问令牌"""
    from app.core.security import create_access_token
    access_token = create_access_token(data={"sub": created_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def superuser_token(created_superuser):
    """超级用户访问令牌"""
    from app.core.security import create_access_token
    access_token = create_access_token(data={"sub": created_superuser.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def sample_users_data() -> list:
    """批量测试用户数据"""
    return [
        {
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123",
            "full_name": "User One",
            "is_superuser": False
        },
        {
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123",
            "full_name": "User Two",
            "is_superuser": False
        },
        {
            "username": "user3",
            "email": "user3@example.com",
            "password": "password123",
            "full_name": "User Three",
            "is_superuser": False
        }
    ]


@pytest.fixture(scope="function")
def created_users(db: Session, sample_users_data: list):
    """创建批量测试用户"""
    users = []
    for user_data in sample_users_data:
        user_create = UserCreate(**user_data)
        user = user_crud.create(db, obj_in=user_create)
        users.append(user)
    
    yield users
    # 清理在db fixture中自动处理


# 测试数据清理装饰器
def cleanup_test_data(func):
    """测试数据清理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            # 在这里可以添加额外的清理逻辑
            pass
    return wrapper


# 测试配置
@pytest.fixture(scope="session", autouse=True)
def test_config():
    """测试配置"""
    # 设置测试环境配置
    settings.DEBUG = True
    settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    yield
    # 测试结束后恢复配置
