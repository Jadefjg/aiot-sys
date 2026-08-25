"""
固件管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import hashlib
import os
import uuid

from app.db.session import get_db
from app.db.models.user import User
from app.core.config import settings
from app.crud.device import device_crud
from app.crud.firmware import firmware_crud, firmware_upgrade_task_crud
from app.core.dependencies import get_current_active_user, has_permission
from app.tasks.firmware_tasks import initiate_firmware_upgrade
from app.schemas.firmware import Firmware, FirmwareCreate, FirmwareUpgradeTask, FirmwareUpgradeTaskCreate
from app.services import access_control as access


router = APIRouter()


# ==================== 升级任务管理 (放在参数路由之前) ====================

@router.get("/tasks", response_model=List[FirmwareUpgradeTask])
def get_upgrade_tasks(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取升级任务列表（按可见设备过滤）"""
    pks = access.visible_device_pk_ids(db, current_user)
    if device_id is not None and pks is not None and device_id not in list(pks):
        raise HTTPException(status_code=403, detail="权限不足")
    return firmware_upgrade_task_crud.get_multi(
        db, skip=skip, limit=limit, device_id=device_id, status=status, device_ids=pks
    )


@router.get("/tasks/{task_id}", response_model=FirmwareUpgradeTask)
def get_upgrade_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取升级任务状态"""
    task = firmware_upgrade_task_crud.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="升级任务不存在")
    device = device_crud.get(db, id=task.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    access.ensure_device(db, current_user, device, "viewer")
    return task


@router.post("/tasks", response_model=FirmwareUpgradeTask, status_code=status.HTTP_202_ACCEPTED)
async def create_upgrade_task(
    task_in: FirmwareUpgradeTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """创建固件升级任务"""
    device = device_crud.get(db, id=task_in.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    access.ensure_device(db, current_user, device, "operator")

    firmware = firmware_crud.get(db, id=task_in.firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")
    if firmware.product_id and device.product_id and firmware.product_id != device.product_id:
        raise HTTPException(status_code=400, detail="固件产品与设备产品不匹配")
    access.ensure_product(db, current_user, firmware.product_id, "operator")

    task = firmware_upgrade_task_crud.create(db, obj_in=task_in, created_by=current_user.id)

    try:
        celery_task = initiate_firmware_upgrade.delay(task.id)
        firmware_upgrade_task_crud.update_celery_task_id(db, task.id, celery_task.id)
    except Exception as e:
        firmware_upgrade_task_crud.update_status(db, task.id, "failed", error_message=str(e))

    return task


@router.post("/tasks/{task_id}/cancel", response_model=FirmwareUpgradeTask)
def cancel_upgrade_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """取消升级任务"""
    task = firmware_upgrade_task_crud.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="升级任务不存在")
    device = device_crud.get(db, id=task.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    access.ensure_device(db, current_user, device, "operator")

    if task.status not in ["pending", "in_progress"]:
        raise HTTPException(status_code=400, detail="该任务无法取消")

    return firmware_upgrade_task_crud.cancel_task(db, id=task_id)


@router.delete("/tasks/{task_id}", response_model=FirmwareUpgradeTask)
def delete_upgrade_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """删除升级任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")

    task = firmware_upgrade_task_crud.get(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="升级任务不存在")

    return firmware_upgrade_task_crud.delete(db, id=task_id)


# ==================== 固件管理 ====================

@router.get("/", response_model=List[Firmware])
def get_firmwares(
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取固件列表（按可见产品过滤）"""
    if product_id:
        access.ensure_product(db, current_user, product_id, "viewer")
        return firmware_crud.get_multi(db, skip=skip, limit=limit, product_id=product_id)
    rows = firmware_crud.get_multi(db, skip=0, limit=500)
    if not current_user.is_superuser:
        allowed = set(access.visible_product_ids(db, current_user))
        rows = [r for r in rows if r.product_id in allowed]
    return rows[skip:skip + limit]


@router.get("/{firmware_id}", response_model=Firmware)
def get_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """根据ID获取固件"""
    firmware = firmware_crud.get(db, id=firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")
    access.ensure_product(db, current_user, firmware.product_id, "viewer")
    return firmware


@router.post("/upload", response_model=Firmware, status_code=status.HTTP_201_CREATED)
async def upload_firmware(
    file: UploadFile = File(...),
    product_id: str = Form(...),
    version: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """上传固件文件"""
    access.ensure_product(db, current_user, product_id, "operator")
    # 检查版本是否已存在
    existing = firmware_crud.get_by_version_and_product(db, version=version, product_id=product_id)
    if existing:
        raise HTTPException(status_code=400, detail="该产品的固件版本已存在")

    # 保存固件文件
    upload_dir = settings.FIRMWARE_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = os.path.basename(file.filename or "firmware.bin")
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_location = os.path.join(upload_dir, stored_name)

    file_hash = hashlib.sha256()
    file_size = 0

    with open(file_location, "wb") as f:
        while contents := await file.read(1024 * 1024):
            f.write(contents)
            file_hash.update(contents)
            file_size += len(contents)

    file_hash_str = file_hash.hexdigest()

    # 创建固件记录
    firmware_in = FirmwareCreate(
        version=version,
        product_id=product_id,
        file_url=f"{settings.FIRMWARE_BASE_URL}/{stored_name}",
        file_hash=file_hash_str,
        description=description
    )

    return firmware_crud.create(
        db=db,
        obj_in=firmware_in,
        created_by=current_user.id,
        file_name=file.filename,
        file_path=file_location,
        file_size=file_size
    )


@router.put("/{firmware_id}", response_model=Firmware)
def update_firmware(
    firmware_id: int,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_beta: Optional[bool] = None,
    release_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """更新固件信息"""
    firmware = firmware_crud.get(db, id=firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")
    access.ensure_product(db, current_user, firmware.product_id, "operator")

    return firmware_crud.update(
        db,
        db_obj=firmware,
        description=description,
        is_active=is_active,
        is_beta=is_beta,
        release_notes=release_notes
    )


@router.delete("/{firmware_id}", response_model=Firmware)
def delete_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """删除固件"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")

    firmware = firmware_crud.get(db, id=firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")

    # 删除物理文件
    if firmware.file_path and os.path.exists(firmware.file_path):
        try:
            os.remove(firmware.file_path)
        except OSError:
            pass  # 忽略文件删除错误

    return firmware_crud.delete(db, id=firmware_id)


@router.get("/product/{product_id}/latest", response_model=Firmware)
def get_latest_firmware(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取产品的最新固件"""
    access.ensure_product(db, current_user, product_id, "viewer")
    firmware = firmware_crud.get_latest_firmware(db, product_id=product_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="未找到该产品的固件")
    return firmware
