import json
import time
from celery import Celery

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.device import device_crud
from app.crud.firmware import firmware_crud
from app.db.models.firmware import FirmwareUpgradeTask
from app.services.mqtt_service import mqtt_client


celery_app = Celery(
    'firmware_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


@celery_app.task(bind=True)
def initiate_firmware_upgrade(self, task_id: int):
    db = SessionLocal()
    try:
        upgrade_task = firmware_crud.get_upgrade_task(db, task_id)
        if not upgrade_task:
            print(f"Upgrade task {task_id} not found.")
            return

        device = device_crud.get_device(db, upgrade_task.device_id)
        firmware = firmware_crud.get_firmware(db, upgrade_task.firmware_id)

        if not device or not firmware:
            firmware_crud.upgrade_task_status(db, upgrade_task, "failed", error_message="Device or Firmware not found.")
            return

        # 更新任务状态为进行中
        firmware_crud.update_upgrade_task_status(db, upgrade_task, "in_progress", progress=0)
        # 1. 向设备发送升级通知 (通过MQTT)
        mqtt_topic = f"device/{device.device_id}/firmware/upgrade"
        upgrade_payload = {
            "version": firmware.version,
            "file_url": firmware.file_url,
            "file_hash": firmware.file_hash,
        }
        mqtt_client.publish(mqtt_topic, json.dumps(upgrade_payload))
        print(f"Sent upgrade command to device {device.device_id}")

        # 2. 模拟设备升级过程 (实际中设备会通过MQTT上报进度和状态)
        # 在实际应用中，这里会有一个循环，等待设备上报状态，并更新数据库
        # 为了演示，我们模拟一个延时和进度更新
        for i in range(1, 11):
            time.sleep(2)  # 模拟下载/安装时间
        progress = i * 10
        firmware_crud.update_upgrade_task_progress(db, upgrade_task,progress)
        self.update_state(state='PROGRESS', meta={'progress': progress})
        print(f"Device {device.device_id} upgrade progress: {progress}%")

        # 3. 假设设备升级成功
        firmware_crud.update_upgrade_task_status(db, upgrade_task, "success",progress=100)

        # 更新设备表中的固件版本
        device_crud.update_device(db, device, DeviceUpdate(firmware_version=firmware.version))
        print(f"Firmware upgrade for device {device.device_id} completed,successfully.")
    except Exception as e:
        print(f"Firmware upgrade task {task_id} failed: {e}")
        firmware_crud.update_upgrade_task_status(db, upgrade_task, "failed",error_message=str(e))
    finally:
        db.close()

