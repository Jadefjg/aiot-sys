import json
import time
import requests
import hashlib
from typing import Optional
from datetime import datetime
from celery import Celery
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_crud
from app.crud.firmware import firmware_crud
from app.services.mqtt_service import mqtt_service


# 创建Celery应用
celery_app = Celery(
    "firmware_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.firmware_tasks"]
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

@celery_app.task(bind=True, name="firmware_tasks.initiate_firmware_upgrade")
def initiate_firmware_upgrade(self, task_id: int):
    """启动固件升级任务"""
    db = SessionLocal()
    try:
        # 获取升级任务
        upgrade_task = firmware_crud.get_upgrade_task(db, task_id)
        if not upgrade_task:
            logger.error(f"Upgrade task {task_id} not found")
            return {"status": "failed", "error": "Task not found"}
        device = device_crud.get(db, upgrade_task.device_id)
        firmware = firmware_crud.get(db, upgrade_task.firmware_id)
        if not device or not firmware:
            error_msg = "Device or Firmware not found"
            firmware_crud.update_upgrade_task_status(db, upgrade_task, "failed", error_message=error_msg)
            logger.error(f"Task {task_id}: {error_msg}")
            return {"status": "failed", "error": error_msg}
        logger.info(f"Starting firmware upgrade for device {device.device_id} to version {firmware.version}")
        # 更新任务状态为进行中
        firmware_crud.update_upgrade_task_status(db, upgrade_task,"in_progress", progress=0)
        # 1. 验证固件文件
        self.update_state(state='PROGRESS', meta={'progress': 5, 'status':'Validating firmware'})
        if not _validate_firmware_file(firmware):
            error_msg = "Firmware file validation failed"
            firmware_crud.update_upgrade_task_status(
                db, upgrade_task, "failed", error_message=error_msg
            )
            logger.error(f"Task {task_id}: {error_msg}")
            return {"status": "failed", "error": error_msg}

        # 2. 检查设备状态
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status':'Checking device status'})
        if device.status != "online":
            error_msg = f"Device is not online (status: {device.status})"
            firmware_crud.update_upgrade_task_status(
                db, upgrade_task, "failed", error_message=error_msg
            )
            logger.error(f"Task {task_id}: {error_msg}")
            return {"status": "failed", "error": error_msg}

        # 3. 向设备发送升级通知
        self.update_state(state='PROGRESS', meta={'progress': 15, 'status':'Sending upgrade command'})
        upgrade_command = {
            "task_id": task_id,
            "firmware_version": firmware.version,
            "firmware_url": firmware.file_url,
            "firmware_hash": firmware.file_hash,
            "firmware_size": firmware.file_size
        }
        topic = f"device/{device.device_id}/firmware/upgrade"
        try:
            mqtt_service.publish(topic, json.dumps(upgrade_command))
            logger.info(f"Sent upgrade command to device {device.device_id}")
        except Exception as e:
            error_msg = f"Failed to send upgrade command: {str(e)}"
            firmware_crud.update_upgrade_task_status(
                db, upgrade_task, "failed", error_message=error_msg
            )
            logger.error(f"Task {task_id}: {error_msg}")
        return {"status": "failed", "error": error_msg}

        # 4. 等待设备响应和升级过程
        max_wait_time = 1800 # 30分钟
        check_interval = 10 # 10秒检查一次
        waited_time = 0

        while waited_time < max_wait_time:
            time.sleep(check_interval)
            waited_time += check_interval
            # 刷新任务状态
            db.refresh(upgrade_task)
        progress = min(15 + (waited_time / max_wait_time) * 80, 95)
        self.update_state(
            state='PROGRESS',
            meta={
                'progress': int(progress),
                'status': f'Waiting for device response({upgrade_task.status})'
            }
        )
        if upgrade_task.status == "success":
            logger.info(f"Task {task_id}: Firmware upgrade completed successfully")
            # 更新设备固件版本
            device_crud.update(db, device, {"firmware_version":firmware.version})
            return {"status": "success", "message": "Firmware upgrade completed"}
        elif upgrade_task.status == "failed":
            logger.error(f"Task {task_id}: Firmware upgrade failed:{upgrade_task.error_message}")
            return {"status": "failed", "error":upgrade_task.error_message}
        elif upgrade_task.status == "cancelled":
            logger.info(f"Task {task_id}: Firmware upgrade was cancelled")
            return {"status": "cancelled", "message": "Firmware upgrade was cancelled"}
            # 超时处理
            error_msg = "Firmware upgrade timeout"
            firmware_crud.update_upgrade_task_status(db, upgrade_task, "failed", error_message=error_msg)
            logger.error(f"Task {task_id}: {error_msg}")
            return {"status": "failed", "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Task {task_id}: {error_msg}")
        try:
            firmware_crud.update_upgrade_task_status(db, upgrade_task, "failed", error_message=error_msg)
        except:
            pass
        return {"status": "failed", "error": error_msg}
    finally:
        db.close()

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
            latest_firmware = firmware_crud.get_latest_firmware_for_product(db, device.product_id)
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