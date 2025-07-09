from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List,Optional
import hashlib
import os

from app.db.session import get_db
from app.core.config import settings
from app.crud.device import device_crud
from app.crud.firmware import firmware_crud # 假设已定义CRUDFirmware
from app.core.security import get_current_active_user, has_permission
from app.tasks.firmware_tasks import celery_app, initiate_firmware_upgrade
from app.schemas.firmware import Firmware, FirmwareCreate, FirmwareUpgradeTask,FirmwareUpgradeTaskCreate


router = APIRouter()


@router.post(
    "/firmwares/upload",
     response_model=Firmware,
     status_code=status.HTTP_201_CREATED,
     dependencies=[Depends(has_permission("firmware:upload"))])
async def upload_firmware_file(
        product_id: str,
        version: str,
        description: Optional[str] = None,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
    ):
    # 1. 保存固件文件到本地或对象存储
    upload_dir = settings.FIRMWARE_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    file_location = os.path.join(upload_dir, file.filename)
    file_hash = None
    with open(file_location, "wb") as f:
        while contents := file.file.read(1024 * 1024):
            f.write(contents)
            # 同时计算文件哈希
            if file_hash is None:
                file_hash = hashlib.sha256()
            file_hash.update(contents)
    file_hash_str = file_hash.hexdigest() if file_hash else None
    # 2. 记录固件信息到数据库
    firmware_in = FirmwareCreate(
        version=version,
        product_id=product_id,
        file_url=f"{settings.FIRMWARE_BASE_URL}/{file.filename}", # 假设Nginx或其他服务提供下载
        file_hash=file_hash_str,
        description=description
    )
    db_firmware = firmware_crud.get_firmware_by_version_and_product(db,version=version, product_id=product_id)
    if db_firmware:
        raise HTTPException(status_code=400, detail="Firmware version for this product already exists")
    return firmware_crud.create_firmware(db=db, firmware=firmware_in)


@router.post(
    "/firmware_upgrade_tasks/initiate",
    response_model=FirmwareUpgradeTask,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(has_permission("firmware:upgrade"))])
async def create_firmware_upgrade_task(
    task_in: FirmwareUpgradeTaskCreate,
    db: Session = Depends(get_db),
    ):
    device = device_crud.get_device(db, task_in.device_id)
    firmware = firmware_crud.get_firmware(db, task_in.firmware_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")
    # 创建升级任务记录
    db_task = firmware_crud.create_upgrade_task(db=db, task=task_in)
    # 异步启动固件升级任务
    celery_task = initiate_firmware_upgrade.delay(db_task.id)
    # 可以将 celery_task.id 存储到 db_task 中，以便后续查询Celery任务状态
    firmware_crud.update_upgrade_task_celery_id(db, db_task, celery_task.id)
    return db_task


@router.get(
    "/firmware_upgrade_tasks/{task_id}",
    response_model=FirmwareUpgradeTask, dependencies=[Depends(has_permission("firmware:read_task"))])
def get_firmware_upgrade_task_status(
    task_id: int,
    db: Session = Depends(get_db),
    ):
    upgrade_task = firmware_crud.get_upgrade_task(db, task_id)
    if not upgrade_task:
        raise HTTPException(status_code=404, detail="Upgrade task not found")
    # 可以从Celery获取实时进度，但这里简化为只从数据库读取
    return upgrade_task
# ... 其他固件管理API，如获取固件列表，删除固件


