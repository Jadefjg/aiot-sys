"""MQTT 分发与固件 OTA 轮询修复"""
from unittest.mock import MagicMock, patch

from app.services.mqtt_service import MQTTService
from app.schemas.device import DeviceUpdate


def test_push_values_dispatches_to_handle_values():
    svc = MQTTService()
    with patch.object(svc, "_handle_values") as handle_values, patch.object(
        svc, "_handle_event"
    ) as handle_event:
        svc._process("push/dev-1/values", b'{"battery": 9}')
        handle_values.assert_called_once_with("dev-1", '{"battery": 9}')
        handle_event.assert_not_called()


def test_legacy_command_id_accepts_string():
    svc = MQTTService()
    db = MagicMock()
    with patch("app.services.mqtt_service.SessionLocal", return_value=db), patch(
        "app.services.mqtt_service.device_command_crud"
    ) as crud:
        svc._handle_legacy_command("dev-1", '{"command_id": "12", "status": "acknowledged"}')
        crud.update_status.assert_called_once()
        assert crud.update_status.call_args[0][1] == 12


def test_firmware_status_updates_task():
    svc = MQTTService()
    db = MagicMock()
    with patch("app.services.mqtt_service.SessionLocal", return_value=db), patch(
        "app.crud.firmware.firmware_upgrade_task_crud"
    ) as crud:
        svc._handle_firmware(
            "dev-1",
            '{"task_id": 8, "status": "in_progress", "progress": 40}',
        )
        crud.update_status.assert_called_once_with(
            db, 8, "in_progress", progress=40, error_message=None
        )


def test_firmware_success_updates_device_version():
    svc = MQTTService()
    db = MagicMock()
    device = MagicMock()
    with patch("app.services.mqtt_service.SessionLocal", return_value=db), patch(
        "app.crud.firmware.firmware_upgrade_task_crud"
    ), patch("app.services.mqtt_service.device_crud") as device_crud:
        device_crud.get_by_device_id.return_value = device
        svc._handle_firmware(
            "dev-1",
            '{"task_id": 8, "status": "success", "progress": 100, "version": "2.0.0"}',
        )
        device_crud.update.assert_called_once()
        args = device_crud.update.call_args[0]
        assert args[1] is device
        assert isinstance(args[2], DeviceUpdate)
        assert args[2].firmware_version == "2.0.0"


def test_poll_upgrade_success_updates_device_version():
    from celery_worker import _poll_upgrade_result

    task = MagicMock(status="success", device_id=1, error_message=None)
    device = MagicMock()
    firmware = MagicMock(version="1.2.3")
    celery_task = MagicMock()
    with patch("celery_worker.SessionLocal") as session_local, patch(
        "celery_worker.firmware_upgrade_task_crud"
    ) as crud, patch("celery_worker.device_crud") as device_crud, patch(
        "celery_worker.time.sleep"
    ):
        session_local.return_value = MagicMock()
        crud.get.return_value = task
        device_crud.get.return_value = device
        result = _poll_upgrade_result(celery_task, 9, firmware, max_wait=10, interval=10)
        assert result["status"] == "success"
        device_crud.update.assert_called_once()
        assert isinstance(device_crud.update.call_args[0][2], DeviceUpdate)
        assert device_crud.update.call_args[0][2].firmware_version == "1.2.3"
