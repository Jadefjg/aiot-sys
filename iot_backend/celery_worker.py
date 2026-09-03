import time
import requests
from celery import Celery
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_crud
from app.crud.firmware import firmware_crud, firmware_upgrade_task_crud
from app.schemas.device import DeviceUpdate
from app.services.mqtt_service import mqtt_service


# 创建Celery应用
celery_app = Celery(
    "firmware_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.firmware_tasks", "app.tasks.media_tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60, # 30分钟超时
    task_soft_time_limit=25 * 60, # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

logger = get_task_logger(__name__)

def _fail_upgrade(db, task_id: int, message: str) -> dict:
    firmware_upgrade_task_crud.update_status(db, task_id, "failed", error_message=message)
    logger.error("Task %s: %s", task_id, message)
    return {"status": "failed", "error": message}


def _poll_upgrade_result(celery_task, task_id: int, firmware, max_wait: int = 1800, interval: int = 10) -> dict:
    """独立会话轮询，避免 MySQL REPEATABLE READ 看不到 MQTT 回写"""
    waited = 0
    while waited < max_wait:
        time.sleep(interval)
        waited += interval
        db = SessionLocal()
        try:
            task = firmware_upgrade_task_crud.get(db, id=task_id)
            if not task:
                return {"status": "failed", "error": "Task not found"}
            celery_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": int(min(15 + (waited / max_wait) * 80, 95)),
                    "status": f"Waiting for device response({task.status})",
                },
            )
            if task.status == "success":
                device = device_crud.get(db, task.device_id)
                if device:
                    device_crud.update(db, device, DeviceUpdate(firmware_version=firmware.version))
                logger.info("Task %s: Firmware upgrade completed successfully", task_id)
                return {"status": "success", "message": "Firmware upgrade completed"}
            if task.status == "failed":
                return {"status": "failed", "error": task.error_message}
            if task.status == "cancelled":
                return {"status": "cancelled", "message": "Firmware upgrade was cancelled"}
        finally:
            db.close()
    db = SessionLocal()
    try:
        return _fail_upgrade(db, task_id, "Firmware upgrade timeout")
    finally:
        db.close()


@celery_app.task(bind=True, name="firmware_tasks.initiate_firmware_upgrade")
def initiate_firmware_upgrade(self, task_id: int):
    """启动固件升级任务"""
    firmware = None
    published = False
    db = SessionLocal()
    try:
        upgrade_task = firmware_upgrade_task_crud.get(db, id=task_id)
        if not upgrade_task:
            logger.error("Upgrade task %s not found", task_id)
            return {"status": "failed", "error": "Task not found"}
        device = device_crud.get(db, upgrade_task.device_id)
        firmware = firmware_crud.get(db, upgrade_task.firmware_id)
        if not device or not firmware:
            return _fail_upgrade(db, task_id, "Device or Firmware not found")
        logger.info(
            "Starting firmware upgrade for device %s to version %s",
            device.device_id, firmware.version,
        )
        firmware_upgrade_task_crud.update_status(db, task_id, "in_progress", progress=0)
        self.update_state(state="PROGRESS", meta={"progress": 5, "status": "Validating firmware"})
        if not _validate_firmware_file(firmware):
            return _fail_upgrade(db, task_id, "Firmware file validation failed")
        self.update_state(state="PROGRESS", meta={"progress": 10, "status": "Checking device status"})
        if device.status != "online":
            return _fail_upgrade(db, task_id, f"Device is not online (status: {device.status})")
        self.update_state(state="PROGRESS", meta={"progress": 15, "status": "Sending upgrade command"})
        command = {
            "task_id": task_id,
            "firmware_version": firmware.version,
            "firmware_url": firmware.file_url,
            "firmware_hash": firmware.file_hash,
            "firmware_size": firmware.file_size,
        }
        if not mqtt_service.publish(f"device/{device.device_id}/firmware/upgrade", command):
            return _fail_upgrade(db, task_id, "Failed to send upgrade command")
        logger.info("Sent upgrade command to device %s", device.device_id)
        published = True
    except Exception as exc:
        error_msg = f"Unexpected error: {exc}"
        logger.error("Task %s: %s", task_id, error_msg)
        try:
            firmware_upgrade_task_crud.update_status(db, task_id, "failed", error_message=error_msg)
        except Exception:
            pass
        return {"status": "failed", "error": error_msg}
    finally:
        db.close()
    if published and firmware:
        return _poll_upgrade_result(self, task_id, firmware)
    return {"status": "failed", "error": "Task aborted"}

@celery_app.task(name="firmware_tasks.cleanup_old_firmware_files")
def cleanup_old_firmware_files():
    """理旧的固件文件"""
    logger.info("Starting firmware file cleanup task")
    # 实现清理逻辑
    # 例如：删除超过30天且没有被引用的固件文件
    pass

@celery_app.task(name="firmware_tasks.check_device_firmware_updates")
def check_device_firmware_updates():
    """检查设备是否有可用的固件更新"""
    logger.info("Checking for device firmware updates")
    db = SessionLocal()
    try:
        # 获取所有在线设备
        online_devices = device_crud.get_online_devices(db)
        for device in online_devices:
            # 检查是否有更新的固件版本
            latest_firmware = firmware_crud.get_latest_firmware(db, device.product_id)
            if (latest_firmware and latest_firmware.version != device.firmware_version and latest_firmware.is_active):
                logger.info(f"Device {device.device_id} has firmware update available:"f"{device.firmware_version} -> {latest_firmware.version}")
        # 这里可以发送通知或自动创建升级任务
        # 具体策略根据业务需求决定
    except Exception as e:
        logger.error(f"Error checking firmware updates: {e}")
    finally:
        db.close()

def _validate_firmware_file(firmware) -> bool:
    """验证固件文件的完整性"""
    try:
        # 检查文件是否存在
        response = requests.head(firmware.file_url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Firmware file not accessible: {firmware.file_url}")
            return False
        # 检查文件大小
        content_length = response.headers.get('content-length')
        if content_length and firmware.file_size:
            if int(content_length) != firmware.file_size:
                logger.error(f"Firmware file size mismatch")
                return False

        # 如果有哈希值，验证文件哈希
        if firmware.file_hash:
            # 这里可以下载文件并验证哈希
            # 为了简化，暂时跳过实际下载验证
            pass
        return True
    except Exception as e:
        logger.error(f"Error validating firmware file: {e}")
        return False

# Celery启动时的配置
if __name__ == '__main__':
    celery_app.start()