"""
固件升级任务模块

从 celery_worker.py 导入 Celery 应用和任务，避免代码重复。
"""

from celery_worker import (
    celery_app,
    initiate_firmware_upgrade,
    cleanup_old_firmware_files,
    check_device_firmware_updates,
)

__all__ = [
    "celery_app",
    "initiate_firmware_upgrade",
    "cleanup_old_firmware_files",
    "check_device_firmware_updates",
]
