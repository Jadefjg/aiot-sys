"""
设备CRUD模块单元测试
测试 app/crud/device.py 中的 CRUDDevice, CRUDDeviceData, CRUDDeviceCommand 类
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.crud.device import CRUDDevice, CRUDDeviceData, CRUDDeviceCommand
from app.db.models.device import Device, DeviceData, DeviceCommand
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceDataCreate, DeviceCommandCreate


class TestCRUDDevice:
    """CRUDDevice 类的单元测试"""

    @pytest.fixture
    def crud_device(self):
        """创建 CRUDDevice 实例"""
        return CRUDDevice()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_device(self):
        """创建模拟的 Device 对象"""
        device = MagicMock(spec=Device)
        device.id = 1
        device.device_id = "device001"
        device.device_name = "Test Device"
        device.product_id = "product001"
        device.owner_id = 1
        device.status = "online"
        device.last_online_at = datetime.utcnow()
        return device

    @pytest.fixture
    def device_create_data(self):
        """创建设备数据"""
        return DeviceCreate(
            device_id="device002",
            device_name="New Device",
            product_id="product001",
            owner_id=1
        )

    def test_get_device_by_id_success(self, crud_device, mock_db, mock_device):
        """测试通过ID获取设备 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device

        # 执行测试
        result = crud_device.get(mock_db, id=1)

        # 验证结果
        assert result == mock_device
        mock_db.query.assert_called_once_with(Device)

    def test_get_device_by_id_not_found(self, crud_device, mock_db):
        """测试通过ID获取设备 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_device.get(mock_db, id=999)

        # 验证结果
        assert result is None

    def test_get_by_device_id_success(self, crud_device, mock_db, mock_device):
        """测试通过设备ID获取设备 - 成功"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device

        # 执行测试
        result = crud_device.get_by_device_id(mock_db, device_id="device001")

        # 验证结果
        assert result == mock_device
        assert result.device_id == "device001"

    def test_get_multi_devices_no_owner(self, crud_device, mock_db, mock_device):
        """测试获取设备列表 - 无所有者过滤"""
        # 配置模拟
        mock_devices = [mock_device, mock_device]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_devices

        # 执行测试
        result = crud_device.get_multi(mock_db, skip=0, limit=10, owner_id=None)

        # 验证结果
        assert len(result) == 2
        mock_db.query.assert_called_once_with(Device)

    def test_get_multi_devices_with_owner(self, crud_device, mock_db, mock_device):
        """测试获取设备列表 - 按所有者过滤"""
        # 配置模拟
        mock_devices = [mock_device]
        query_mock = mock_db.query.return_value
        query_mock.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_devices

        # 执行测试
        result = crud_device.get_multi(mock_db, skip=0, limit=10, owner_id=1)

        # 验证结果
        assert len(result) == 1
        query_mock.filter.assert_called_once()

    def test_get_by_product(self, crud_device, mock_db, mock_device):
        """测试按产品ID获取设备列表"""
        # 配置模拟
        mock_devices = [mock_device, mock_device]
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_devices

        # 执行测试
        result = crud_device.get_by_product(mock_db, product_id="product001", skip=0, limit=10)

        # 验证结果
        assert len(result) == 2

    def test_create_device_success(self, crud_device, mock_db, device_create_data):
        """测试创建设备 - 成功"""
        # 配置模拟
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_device.create(mock_db, obj_in=device_create_data)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_device_success(self, crud_device, mock_db, mock_device):
        """测试更新设备 - 成功"""
        # 配置模拟
        update_data = DeviceUpdate(device_name="Updated Device", status="offline")

        # 执行测试
        result = crud_device.update(mock_db, db_obj=mock_device, obj_in=update_data)

        # 验证结果
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_delete_device_success(self, crud_device, mock_db, mock_device):
        """测试删除设备 - 成功"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = mock_device

        # 执行测试
        result = crud_device.delete(mock_db, id=1)

        # 验证结果
        assert result == mock_device
        mock_db.delete.assert_called_once_with(mock_device)
        mock_db.commit.assert_called_once()

    def test_delete_device_not_found(self, crud_device, mock_db):
        """测试删除设备 - 未找到"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = None

        # 执行测试
        result = crud_device.delete(mock_db, id=999)

        # 验证结果
        assert result is None
        mock_db.delete.assert_not_called()

    @patch('app.crud.device.datetime')
    def test_update_status_online(self, mock_datetime, crud_device, mock_db, mock_device):
        """测试更新设备状态 - 上线"""
        # 配置模拟
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device

        # 执行测试
        result = crud_device.update_status(mock_db, device_id="device001", status="online")

        # 验证结果
        assert result == mock_device
        mock_db.commit.assert_called_once()

    def test_update_status_offline(self, crud_device, mock_db, mock_device):
        """测试更新设备状态 - 离线"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device

        # 执行测试
        result = crud_device.update_status(mock_db, device_id="device001", status="offline")

        # 验证结果
        assert result == mock_device
        mock_db.commit.assert_called_once()

    def test_update_status_device_not_found(self, crud_device, mock_db):
        """测试更新设备状态 - 设备未找到"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # 执行测试
        result = crud_device.update_status(mock_db, device_id="nonexistent", status="online")

        # 验证结果
        assert result is None

    def test_get_online_devices(self, crud_device, mock_db, mock_device):
        """测试获取在线设备列表"""
        # 配置模拟
        mock_devices = [mock_device, mock_device]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_devices

        # 执行测试
        result = crud_device.get_online_devices(mock_db)

        # 验证结果
        assert len(result) == 2

    @patch('app.crud.device.datetime')
    def test_get_offline_devices(self, mock_datetime, crud_device, mock_db, mock_device):
        """测试获取离线设备列表"""
        # 配置模拟
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_devices = [mock_device]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_devices

        # 执行测试
        result = crud_device.get_offline_devices(mock_db, minutes=30)

        # 验证结果
        assert len(result) == 1


class TestCRUDDeviceData:
    """CRUDDeviceData 类的单元测试"""

    @pytest.fixture
    def crud_device_data(self):
        """创建 CRUDDeviceData 实例"""
        return CRUDDeviceData()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_device(self):
        """创建模拟的 Device 对象"""
        device = MagicMock(spec=Device)
        device.id = 1
        device.device_id = "device001"
        return device

    @pytest.fixture
    def mock_device_data(self):
        """创建模拟的 DeviceData 对象"""
        data = MagicMock(spec=DeviceData)
        data.id = 1
        data.device_id = 1
        data.timestamp = datetime.utcnow()
        data.data = {"temperature": 25.5}
        return data

    @pytest.fixture
    def device_data_create(self):
        """创建设备数据"""
        return DeviceDataCreate(
            device_id="device001",
            data={"temperature": 25.5, "humidity": 60}
        )

    @patch('app.crud.device.device_crud')
    def test_create_device_data_success(self, mock_device_crud, crud_device_data, mock_db, mock_device, device_data_create):
        """测试创建设备数据 - 成功"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = mock_device
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_device_data.create(mock_db, obj_in=device_data_create)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.crud.device.device_crud')
    def test_create_device_data_device_not_found(self, mock_device_crud, crud_device_data, mock_db, device_data_create):
        """测试创建设备数据 - 设备未找到"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = None

        # 执行测试
        result = crud_device_data.create(mock_db, obj_in=device_data_create)

        # 验证结果
        assert result is None
        mock_db.add.assert_not_called()

    def test_get_device_data(self, crud_device_data, mock_db, mock_device_data):
        """测试获取设备数据列表"""
        # 配置模拟
        mock_data_list = [mock_device_data, mock_device_data]
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_data_list

        # 执行测试
        result = crud_device_data.get_device_data(mock_db, device_id=1, skip=0, limit=10)

        # 验证结果
        assert len(result) == 2

    def test_get_latest_data(self, crud_device_data, mock_db, mock_device_data):
        """测试获取最新设备数据"""
        # 配置模拟
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_device_data

        # 执行测试
        result = crud_device_data.get_latest_data(mock_db, device_id=1)

        # 验证结果
        assert result == mock_device_data

    def test_get_data_by_time_range(self, crud_device_data, mock_db, mock_device_data):
        """测试按时间范围获取设备数据"""
        # 配置模拟
        mock_data_list = [mock_device_data]
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        end_time = datetime(2024, 1, 1, 23, 59, 59)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_data_list

        # 执行测试
        result = crud_device_data.get_data_by_time_range(mock_db, device_id=1, start_time=start_time, end_time=end_time)

        # 验证结果
        assert len(result) == 1


class TestCRUDDeviceCommand:
    """CRUDDeviceCommand 类的单元测试"""

    @pytest.fixture
    def crud_device_command(self):
        """创建 CRUDDeviceCommand 实例"""
        return CRUDDeviceCommand()

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库 Session"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_device(self):
        """创建模拟的 Device 对象"""
        device = MagicMock(spec=Device)
        device.id = 1
        device.device_id = "device001"
        return device

    @pytest.fixture
    def mock_command(self):
        """创建模拟的 DeviceCommand 对象"""
        command = MagicMock(spec=DeviceCommand)
        command.id = 1
        command.device_id = 1
        command.command_type = "reboot"
        command.command_data = {"delay": 10}
        command.status = "pending"
        return command

    @pytest.fixture
    def command_create_data(self):
        """创建命令数据"""
        return DeviceCommandCreate(
            device_id=1,
            command_type="reboot",
            command_data={"delay": 10}
        )

    @patch('app.crud.device.device_crud')
    def test_create_command_success(self, mock_device_crud, crud_device_command, mock_db, mock_device, command_create_data):
        """测试创建设备命令 - 成功"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = mock_device
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        # 执行测试
        result = crud_device_command.create(mock_db, obj_in=command_create_data, created_by=1)

        # 验证结果
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('app.crud.device.device_crud')
    def test_create_command_device_not_found(self, mock_device_crud, crud_device_command, mock_db, command_create_data):
        """测试创建设备命令 - 设备未找到"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = None

        # 执行测试
        result = crud_device_command.create(mock_db, obj_in=command_create_data, created_by=1)

        # 验证结果
        assert result is None
        mock_db.add.assert_not_called()

    @patch('app.crud.device.datetime')
    def test_update_status_sent(self, mock_datetime, crud_device_command, mock_db, mock_command):
        """测试更新命令状态 - 已发送"""
        # 配置模拟
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_db.query.return_value.get.return_value = mock_command

        # 执行测试
        result = crud_device_command.update_status(mock_db, command_id=1, status="sent")

        # 验证结果
        assert result == mock_command
        mock_db.commit.assert_called_once()

    @patch('app.crud.device.datetime')
    def test_update_status_acknowledged(self, mock_datetime, crud_device_command, mock_db, mock_command):
        """测试更新命令状态 - 已确认"""
        # 配置模拟
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_db.query.return_value.get.return_value = mock_command

        # 执行测试
        result = crud_device_command.update_status(
            mock_db,
            command_id=1,
            status="acknowledged",
            response_data={"result": "success"}
        )

        # 验证结果
        assert result == mock_command
        mock_db.commit.assert_called_once()

    def test_update_status_command_not_found(self, crud_device_command, mock_db):
        """测试更新命令状态 - 命令未找到"""
        # 配置模拟
        mock_db.query.return_value.get.return_value = None

        # 执行测试
        result = crud_device_command.update_status(mock_db, command_id=999, status="sent")

        # 验证结果
        assert result is None

    @patch('app.crud.device.device_crud')
    def test_get_pending_commands(self, mock_device_crud, crud_device_command, mock_db, mock_device, mock_command):
        """测试获取待处理命令列表"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = mock_device
        mock_commands = [mock_command, mock_command]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_commands

        # 执行测试
        result = crud_device_command.get_pending_commands(mock_db, device_id="device001")

        # 验证结果
        assert len(result) == 2

    @patch('app.crud.device.device_crud')
    def test_get_pending_commands_device_not_found(self, mock_device_crud, crud_device_command, mock_db):
        """测试获取待处理命令列表 - 设备未找到"""
        # 配置模拟
        mock_device_crud.get_by_device_id.return_value = None

        # 执行测试
        result = crud_device_command.get_pending_commands(mock_db, device_id="nonexistent")

        # 验证结果
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
