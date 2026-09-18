"""真实 SQLite 会话 + MQTT 分发适配器的可靠性集成测试。

这些测试不依赖外部 broker，但会走真实 SQLAlchemy 查询、更新和事务。
设置 MQTT_INTEGRATION_URL 后可在 CI 中由同样的消息体驱动真实 broker 测试。
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.db.models.device import Device, DeviceCommand
from app.db.models.firmware import Firmware, FirmwareUpgradeTask
from app.services.mqtt_service import MQTTService
from app.crud.device import device_command_crud


@pytest.mark.integration
def test_ota_status_from_wrong_device_is_ignored(db):
    device = Device(device_id="ota-dev-1", device_name="OTA", product_id="p1")
    other = Device(device_id="ota-dev-2", device_name="Other", product_id="p1")
    firmware = Firmware(
        version="2.0", product_id="p1", file_name="fw.bin", file_path="/tmp/fw.bin",
        file_url="http://example/fw.bin", file_size=1,
    )
    db.add_all([device, other, firmware]); db.commit()
    task = FirmwareUpgradeTask(device_id=device.id, firmware_id=firmware.id,
                               status="in_progress", progress=20)
    db.add(task); db.commit(); db.refresh(task)

    svc = MQTTService()
    with patch("app.services.mqtt_service.SessionLocal", return_value=db):
        svc._handle_firmware(other.device_id, '{"task_id": %d, "status": "success", "progress": 100}' % task.id)
    db.refresh(task)
    assert task.status == "in_progress"
    assert task.progress == 20


@pytest.mark.integration
def test_expired_command_requeue_does_not_resurrect_ack(db):
    device = Device(device_id="cmd-dev-1", device_name="Command", product_id="p1")
    db.add(device); db.commit(); db.refresh(device)
    command = DeviceCommand(
        device_id=device.id, command_type="control", command_data={"x": 1},
        status="acknowledged", expires_at=datetime.utcnow() - timedelta(seconds=1),
    )
    db.add(command); db.commit(); db.refresh(command)
    assert device_command_crud.requeue_expired(db, command.id, 30) is False
    db.refresh(command)
    assert command.status == "acknowledged"


@pytest.mark.integration
def test_expired_sent_command_is_requeued_once(db):
    device = Device(device_id="cmd-dev-2", device_name="Command", product_id="p1")
    db.add(device); db.commit(); db.refresh(device)
    command = DeviceCommand(
        device_id=device.id, command_type="control", command_data={"x": 1},
        status="sent", retry_count=0, timeout_seconds=7,
        expires_at=datetime.utcnow() - timedelta(seconds=1),
    )
    db.add(command); db.commit(); db.refresh(command)
    assert device_command_crud.requeue_expired(db, command.id, 7) is True
    assert device_command_crud.requeue_expired(db, command.id, 7) is False
    db.refresh(command)
    assert command.status == "pending"
    assert command.retry_count == 1
