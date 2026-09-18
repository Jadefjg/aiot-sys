"""回归测试：OTA 乱序、命令竞态和时序库降级。"""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.crud.firmware import CRUDFirmwareUpgradeTask
from app.services.timeseries import TimeseriesStore


def test_ota_progress_is_monotonic_and_terminal_state_is_immutable():
    crud = CRUDFirmwareUpgradeTask()
    task = MagicMock(status="in_progress", progress=70)
    crud.get = MagicMock(return_value=task)
    db = MagicMock()

    crud.update_progress(db, 1, 40)
    assert task.progress == 70
    assert task.status == "in_progress"

    crud.update_progress(db, 1, 100)
    assert task.progress == 100
    assert task.status == "success"

    crud.update_progress(db, 1, 20)
    assert task.progress == 100
    assert task.status == "success"


def test_influx_query_failure_can_be_detected_for_mysql_fallback():
    store = TimeseriesStore()
    store._failed = False
    with patch.object(store, "_get_client", side_effect=RuntimeError("influx down")):
        assert store.query_series("dev-1") is None


def test_requeue_expired_uses_status_predicate():
    """The SQL update must only target an expired sent command."""
    from app.db.models.device import DeviceCommand

    db = MagicMock()
    result = MagicMock(rowcount=0)
    db.execute.return_value = result
    crud = __import__("app.crud.device", fromlist=["device_command_crud"]).CRUDDeviceCommand()
    assert crud.requeue_expired(db, 9, 30) is False
    statement = db.execute.call_args.args[0]
    assert "status" in str(statement)
