# 固件升级Celery任务

import logging
from celery import Celery
import sys
import os

# 添加proto生成代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../proto/generated'))

from app.core.config import settings
from app.db.session import SessionLocal
from app.crud.firmware import firmware_crud, upgrade_task_crud
from app.schemas.firmware import FirmwareUpgradeTaskUpdate

logger = logging.getLogger(__name__)

# 创建Celery应用
celery_app = Celery(
    "firmware_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3)
def execute_firmware_upgrade(self, task_id: int):
    """
    执行固件升级任务
    通过gRPC调用mqtt-gateway发送升级命令
    """
    db = SessionLocal()
    try:
        # 获取升级任务
        task = upgrade_task_crud.get(db, task_id)
        if not task:
            logger.error(f"Upgrade task {task_id} not found")
            return {"success": False, "error": "Task not found"}

        # 获取固件信息
        firmware = firmware_crud.get(db, task.firmware_id)
        if not firmware:
            upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
                status="failed",
                error_message="Firmware not found"
            ))
            return {"success": False, "error": "Firmware not found"}

        # 更新任务状态为进行中
        upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
            status="in_progress",
            progress=10
        ))

        # 通过gRPC调用mqtt-gateway发送升级命令
        try:
            import grpc
            from mqtt_gateway_pb2 import SendFirmwareUpgradeRequest
            import mqtt_gateway_pb2_grpc

            channel = grpc.insecure_channel(settings.MQTT_GATEWAY_GRPC)
            stub = mqtt_gateway_pb2_grpc.MqttGatewayServiceStub(channel)

            request = SendFirmwareUpgradeRequest(
                device_id=task.device_identifier,
                firmware_version=firmware.version,
                firmware_url=firmware.file_url,
                file_hash=firmware.file_hash or "",
                file_size=firmware.file_size,
                qos=1
            )
            response = stub.SendFirmwareUpgrade(request)
            channel.close()

            if response.success:
                upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
                    status="in_progress",
                    progress=50
                ))
                logger.info(f"Firmware upgrade command sent for task {task_id}")
                return {"success": True, "upgrade_id": response.upgrade_id}
            else:
                upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
                    status="failed",
                    error_message=response.error_message
                ))
                return {"success": False, "error": response.error_message}

        except grpc.RpcError as e:
            error_msg = f"gRPC error: {e}"
            logger.error(error_msg)
            upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
                status="failed",
                error_message=error_msg
            ))
            # 重试
            raise self.retry(exc=e, countdown=60)

    except Exception as e:
        logger.error(f"Error executing firmware upgrade: {e}")
        if task:
            upgrade_task_crud.update(db, task, FirmwareUpgradeTaskUpdate(
                status="failed",
                error_message=str(e)
            ))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task
def check_upgrade_status(task_id: int):
    """检查升级任务状态"""
    db = SessionLocal()
    try:
        task = upgrade_task_crud.get(db, task_id)
        if not task:
            return {"success": False, "error": "Task not found"}

        return {
            "success": True,
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "error_message": task.error_message
        }
    finally:
        db.close()
