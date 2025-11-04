"""
用户CRUD模块单元测试
测试 app/crud/user.py 中的 CRUDUser, CRUDRole, CRUDPermission 类
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.crud.user import CRUDUser, CRUDRole, CRUDPermission
from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.schemas.user import UserCreate, UserUpdate, RoleCreate, PermissionCreate


class TestCRUDUser:
    """CRUDUser 类的单元测试"""

    @pytest.fixture
    def crud_user(self):
        """创建 CRUDUser 实例"""
        return CRUDUser()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """创建模拟的 User 对象"""
        user = MagicMock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.hashed_password = "hashed_password"
        user.is_active = True
        user.is_superuser = False
        return user

    @pytest.fixture
    def user_create_data(self):
        """创建用户数据"""
        return UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            full_name="New User",
            is_superuser=False
        )

    def test_get_user_by_id_success(self, crud_user, mock_db, mock_user):
        """测试通过ID获取用户 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # 执行测试
        result = crud_user.get(mock_db, id=1)

        # 验证结果
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)

    def test_get_user_by_id_not_found(self, crud_user, mock_db):
        """测试通过ID获取用户 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_user.get(mock_db, id=999)

        # 验证结果
        assert result is None

    def test_get_by_username_success(self, crud_user, mock_db, mock_user):
        """测试通过用户名获取用户 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # 执行测试
        result = crud_user.get_by_username(mock_db, username="testuser")

        # 验证结果
        assert result == mock_user
        assert result.username == "testuser"

    def test_get_by_email_success(self, crud_user, mock_db, mock_user):
        """测试通过邮箱获取用户 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # 执行测试
        result = crud_user.get_by_email(mock_db, email="test@example.com")

        # 验证结果
        assert result == mock_user
        assert result.email == "test@example.com"

    def test_get_multi_users(self, crud_user, mock_db, mock_user):
        """测试获取用户列表"""
        # 配置模拟
        mock_users = [mock_user, mock_user]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_users

        # 执行测试
        result = crud_user.get_multi(mock_db, skip=0, limit=10)

        # 验证结果
        assert len(result) == 2
        mock_db.query.assert_called_once_with(User)

    @patch('app.crud.user.get_password_hash')
    def test_create_user_success(self, mock_hash, crud_user, mock_db, user_create_data):
        """测试创建用户 - 成功"""
        # 配置模拟
        mock_hash.return_value = "hashed_password"
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_user.create(mock_db, obj_in=user_create_data)

        # 验证结果
        mock_hash.assert_called_once_with("password123")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.crud.user.get_password_hash')
    def test_update_user_password(self, mock_hash, crud_user, mock_db, mock_user):
        """测试更新用户密码"""
        # 配置模拟
        mock_hash.return_value = "new_hashed_password"
        update_data = UserUpdate(username="testuser", password="newpassword")

        # 执行测试
        result = crud_user.update(mock_db, db_obj=mock_user, obj_in=update_data)

        # 验证结果
        mock_hash.assert_called_once_with("newpassword")
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    def test_delete_user_success(self, crud_user, mock_db, mock_user):
        """测试删除用户 - 成功"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = mock_user

        # 执行测试
        result = crud_user.delete(mock_db, id=1)

        # 验证结果
        assert result == mock_user
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()

    def test_delete_user_not_found(self, crud_user, mock_db):
        """测试删除用户 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = None

        # 执行测试
        result = crud_user.delete(mock_db, id=999)

        # 验证结果
        assert result is None
        mock_db.delete.assert_not_called()

    @patch('app.crud.user.verify_password')
    def test_authenticate_success(self, mock_verify, crud_user, mock_db, mock_user):
        """测试用户认证 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_verify.return_value = True

        # 执行测试
        result = crud_user.authenticate(mock_db, username="testuser", password="correctpassword")

        # 验证结果
        assert result == mock_user
        mock_verify.assert_called_once_with("correctpassword", "hashed_password")

    @patch('app.crud.user.verify_password')
    def test_authenticate_wrong_password(self, mock_verify, crud_user, mock_db, mock_user):
        """测试用户认证 - 密码错误"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_verify.return_value = False

        # 执行测试
        result = crud_user.authenticate(mock_db, username="testuser", password="wrongpassword")

        # 验证结果
        assert result is None

    def test_authenticate_user_not_found(self, crud_user, mock_db):
        """测试用户认证 - 用户不存在"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_user.authenticate(mock_db, username="nonexistent", password="password")

        # 验证结果
        assert result is None

    def test_is_active_true(self, crud_user, mock_user):
        """测试用户是否活跃 - 是"""
        mock_user.is_active = True
        assert crud_user.is_active(mock_user) is True

    def test_is_active_false(self, crud_user, mock_user):
        """测试用户是否活跃 - 否"""
        mock_user.is_active = False
        assert crud_user.is_active(mock_user) is False

    def test_is_superuser_true(self, crud_user, mock_user):
        """测试用户是否超级用户 - 是"""
        mock_user.is_superuser = True
        assert crud_user.is_superuser(mock_user) is True

    def test_is_superuser_false(self, crud_user, mock_user):
        """测试用户是否超级用户 - 否"""
        mock_user.is_superuser = False
        assert crud_user.is_superuser(mock_user) is False

    def test_assign_role_new(self, crud_user, mock_db):
        """测试分配角色 - 新分配"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_user.assign_role(mock_db, user_id=1, role_id=1)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_assign_role_existing(self, crud_user, mock_db):
        """测试分配角色 - 已存在"""
        # 配置模拟
        mock_user_role = MagicMock(spec=UserRole)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_role

        # 执行测试
        result = crud_user.assign_role(mock_db, user_id=1, role_id=1)

        # 验证结果
        assert result == mock_user_role
        mock_db.add.assert_not_called()

    def test_remove_role_success(self, crud_user, mock_db):
        """测试移除角色 - 成功"""
        # 配置模拟
        mock_user_role = MagicMock(spec=UserRole)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_role

        # 执行测试
        result = crud_user.remove_role(mock_db, user_id=1, role_id=1)

        # 验证结果
        assert result is True
        mock_db.delete.assert_called_once_with(mock_user_role)
        mock_db.commit.assert_called_once()

    def test_remove_role_not_found(self, crud_user, mock_db):
        """测试移除角色 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_user.remove_role(mock_db, user_id=1, role_id=1)

        # 验证结果
        assert result is False
        mock_db.delete.assert_not_called()

    def test_get_user_permissions(self, crud_user, mock_db):
        """测试获取用户权限"""
        # 配置模拟
        mock_permissions = [MagicMock(spec=Permission) for _ in range(3)]
        mock_db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_user.get_user_permissions(mock_db, user_id=1)

        # 验证结果
        assert len(result) == 3

    def test_has_permission_true(self, crud_user, mock_db):
        """测试检查用户权限 - 有权限"""
        # 配置模拟
        mock_permission = MagicMock(spec=Permission)
        mock_db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = mock_permission

        # 执行测试
        result = crud_user.has_permission(mock_db, user_id=1, resource="device", action="read")

        # 验证结果
        assert result is True

    def test_has_permission_false(self, crud_user, mock_db):
        """测试检查用户权限 - 无权限"""
        # 配置模拟
        mock_db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_user.has_permission(mock_db, user_id=1, resource="device", action="delete")

        # 验证结果
        assert result is False


class TestCRUDRole:
    """CRUDRole 类的单元测试"""

    @pytest.fixture
    def crud_role(self):
        """创建 CRUDRole 实例"""
        return CRUDRole()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_role(self):
        """创建模拟的 Role 对象"""
        role = MagicMock(spec=Role)
        role.id = 1
        role.name = "admin"
        role.description = "Administrator role"
        return role

    def test_get_role_by_id(self, crud_role, mock_db, mock_role):
        """测试通过ID获取角色"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        # 执行测试
        result = crud_role.get(mock_db, id=1)

        # 验证结果
        assert result == mock_role

    def test_get_role_by_name(self, crud_role, mock_db, mock_role):
        """测试通过名称获取角色"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role

        # 执行测试
        result = crud_role.get_by_name(mock_db, name="admin")

        # 验证结果
        assert result == mock_role
        assert result.name == "admin"

    def test_get_multi_roles(self, crud_role, mock_db, mock_role):
        """测试获取角色列表"""
        # 配置模拟
        mock_roles = [mock_role, mock_role]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_roles

        # 执行测试
        result = crud_role.get_multi(mock_db, skip=0, limit=10)

        # 验证结果
        assert len(result) == 2

    def test_create_role(self, crud_role, mock_db):
        """测试创建角色"""
        # 配置模拟
        role_data = RoleCreate(name="editor", description="Editor role")
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_role.create(mock_db, obj_in=role_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_assign_permission_new(self, crud_role, mock_db):
        """测试为角色分配权限 - 新分配"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_role.assign_permission(mock_db, role_id=1, permission_id=1)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_assign_permission_existing(self, crud_role, mock_db):
        """测试为角色分配权限 - 已存在"""
        # 配置模拟
        mock_role_permission = MagicMock(spec=RolePermission)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role_permission

        # 执行测试
        result = crud_role.assign_permission(mock_db, role_id=1, permission_id=1)

        # 验证结果
        assert result == mock_role_permission
        mock_db.add.assert_not_called()


class TestCRUDPermission:
    """CRUDPermission 类的单元测试"""

    @pytest.fixture
    def crud_permission(self):
        """创建 CRUDPermission 实例"""
        return CRUDPermission()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_permission(self):
        """创建模拟的 Permission 对象"""
        permission = MagicMock(spec=Permission)
        permission.id = 1
        permission.name = "device:read"
        permission.description = "Read device information"
        return permission

    def test_get_permission_by_id(self, crud_permission, mock_db, mock_permission):
        """测试通过ID获取权限"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_permission

        # 执行测试
        result = crud_permission.get(mock_db, id=1)

        # 验证结果
        assert result == mock_permission

    def test_get_permission_by_name(self, crud_permission, mock_db, mock_permission):
        """测试通过名称获取权限"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_permission

        # 执行测试
        result = crud_permission.get_by_name(mock_db, name="device:read")

        # 验证结果
        assert result == mock_permission
        assert result.name == "device:read"

    def test_get_multi_permissions(self, crud_permission, mock_db, mock_permission):
        """测试获取权限列表"""
        # 配置模拟
        mock_permissions = [mock_permission, mock_permission]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=0, limit=10)

        # 验证结果
        assert len(result) == 2

    def test_create_permission(self, crud_permission, mock_db):
        """测试创建权限"""
        # 配置模拟
        permission_data = PermissionCreate(name="device:write", description="Write device information")
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_permission.create(mock_db, obj_in=permission_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
