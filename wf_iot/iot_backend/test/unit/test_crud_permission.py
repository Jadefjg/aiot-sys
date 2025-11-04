"""
权限CRUD模块单元测试
测试 app/crud/permission.py 中的 CRUDPermission 类
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.crud.permission import CRUDPermission
from app.db.models.user import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate


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
        permission.resource = "device"
        permission.action = "read"
        return permission

    @pytest.fixture
    def permission_create_data(self):
        """创建权限数据"""
        return PermissionCreate(
            name="device:write",
            description="Write device information",
            resource="device",
            action="write"
        )

    def test_get_permission_by_id_success(self, crud_permission, mock_db, mock_permission):
        """测试通过ID获取权限 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_permission

        # 执行测试
        result = crud_permission.get(mock_db, permission_id=1)

        # 验证结果
        assert result == mock_permission
        mock_db.query.assert_called_once_with(Permission)

    def test_get_permission_by_id_not_found(self, crud_permission, mock_db):
        """测试通过ID获取权限 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_permission.get(mock_db, permission_id=999)

        # 验证结果
        assert result is None

    def test_get_by_name_success(self, crud_permission, mock_db, mock_permission):
        """测试通过名称获取权限 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_permission

        # 执行测试
        result = crud_permission.get_by_name(mock_db, name="device:read")

        # 验证结果
        assert result == mock_permission
        assert result.name == "device:read"

    def test_get_by_name_not_found(self, crud_permission, mock_db):
        """测试通过名称获取权限 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_permission.get_by_name(mock_db, name="nonexistent:permission")

        # 验证结果
        assert result is None

    def test_get_multi_permissions(self, crud_permission, mock_db, mock_permission):
        """测试获取权限列表"""
        # 配置模拟
        mock_permissions = [mock_permission, mock_permission, mock_permission]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=0, limit=10)

        # 验证结果
        assert len(result) == 3
        mock_db.query.assert_called_once_with(Permission)

    def test_get_multi_permissions_with_pagination(self, crud_permission, mock_db, mock_permission):
        """测试获取权限列表 - 分页"""
        # 配置模拟
        mock_permissions = [mock_permission]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=10, limit=5)

        # 验证结果
        assert len(result) == 1
        mock_db.query.return_value.offset.assert_called_once_with(10)
        mock_db.query.return_value.offset.return_value.limit.assert_called_once_with(5)

    def test_get_by_resource_success(self, crud_permission, mock_db, mock_permission):
        """测试根据资源类型获取权限列表 - 成功"""
        # 配置模拟
        mock_permissions = [mock_permission, mock_permission]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_permission.get_by_resource(mock_db, resource="device")

        # 验证结果
        assert len(result) == 2
        mock_db.query.assert_called_once_with(Permission)

    def test_get_by_resource_empty(self, crud_permission, mock_db):
        """测试根据资源类型获取权限列表 - 空结果"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_by_resource(mock_db, resource="nonexistent")

        # 验证结果
        assert len(result) == 0

    def test_get_by_action_success(self, crud_permission, mock_db, mock_permission):
        """测试根据操作类型获取权限列表 - 成功"""
        # 配置模拟
        mock_permissions = [mock_permission]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_permissions

        # 执行测试
        result = crud_permission.get_by_action(mock_db, action="read")

        # 验证结果
        assert len(result) == 1
        mock_db.query.assert_called_once_with(Permission)

    def test_get_by_action_empty(self, crud_permission, mock_db):
        """测试根据操作类型获取权限列表 - 空结果"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_by_action(mock_db, action="execute")

        # 验证结果
        assert len(result) == 0

    def test_create_permission_success(self, crud_permission, mock_db, permission_create_data):
        """测试创建权限 - 成功"""
        # 配置模拟
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_permission.create(mock_db, obj_in=permission_create_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_permission_success(self, crud_permission, mock_db, mock_permission):
        """测试更新权限 - 成功"""
        # 配置模拟
        update_data = PermissionUpdate(
            description="Updated description",
            action="update"
        )

        # 执行测试
        result = crud_permission.update(mock_db, db_obj=mock_permission, obj_in=update_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_permission_partial(self, crud_permission, mock_db, mock_permission):
        """测试更新权限 - 部分更新"""
        # 配置模拟
        update_data = PermissionUpdate(description="New description")

        # 执行测试
        result = crud_permission.update(mock_db, db_obj=mock_permission, obj_in=update_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_permission_name(self, crud_permission, mock_db, mock_permission):
        """测试更新权限名称"""
        # 配置模拟
        update_data = PermissionUpdate(name="device:delete")

        # 执行测试
        result = crud_permission.update(mock_db, db_obj=mock_permission, obj_in=update_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_permission_success(self, crud_permission, mock_db, mock_permission):
        """测试删除权限 - 成功"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = mock_permission

        # 执行测试
        result = crud_permission.delete(mock_db, permission_id=1)

        # 验证结果
        assert result == mock_permission
        mock_db.delete.assert_called_once_with(mock_permission)
        mock_db.commit.assert_called_once()

    def test_delete_permission_not_found(self, crud_permission, mock_db):
        """测试删除权限 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = None

        # 执行测试
        # 注意：原代码没有检查 obj 是否为 None，这里测试实际行为
        with pytest.raises(AttributeError):
            crud_permission.delete(mock_db, permission_id=999)

    def test_create_permission_with_all_fields(self, crud_permission, mock_db):
        """测试创建权限 - 所有字段"""
        # 准备数据
        permission_data = PermissionCreate(
            name="user:admin",
            description="Full administrative access",
            resource="user",
            action="admin"
        )

        # 配置模拟
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_permission.create(mock_db, obj_in=permission_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_multi_empty_result(self, crud_permission, mock_db):
        """测试获取权限列表 - 空结果"""
        # 配置模拟
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=0, limit=10)

        # 验证结果
        assert len(result) == 0


class TestCRUDPermissionEdgeCases:
    """CRUDPermission 边界情况测试"""

    @pytest.fixture
    def crud_permission(self):
        """创建 CRUDPermission 实例"""
        return CRUDPermission()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    def test_get_multi_with_zero_limit(self, crud_permission, mock_db):
        """测试获取权限列表 - limit为0"""
        # 配置模拟
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=0, limit=0)

        # 验证结果
        assert len(result) == 0

    def test_get_multi_with_large_skip(self, crud_permission, mock_db):
        """测试获取权限列表 - 大的skip值"""
        # 配置模拟
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_multi(mock_db, skip=1000, limit=10)

        # 验证结果
        assert len(result) == 0

    def test_update_permission_empty_data(self, crud_permission, mock_db):
        """测试更新权限 - 空数据"""
        # 配置模拟
        mock_permission = MagicMock(spec=Permission)
        update_data = PermissionUpdate()

        # 执行测试
        result = crud_permission.update(mock_db, db_obj=mock_permission, obj_in=update_data)

        # 验证结果 - 即使没有更新，仍会调用 commit
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_by_resource_special_characters(self, crud_permission, mock_db):
        """测试根据资源类型获取 - 特殊字符"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_by_resource(mock_db, resource="device/sensor")

        # 验证结果
        assert len(result) == 0

    def test_get_by_action_case_sensitive(self, crud_permission, mock_db):
        """测试根据操作类型获取 - 大小写敏感"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # 执行测试
        result = crud_permission.get_by_action(mock_db, action="READ")  # 大写

        # 验证结果
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
