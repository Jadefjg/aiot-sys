# 固件管理API端点

import os
import hashlib
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, UploadFile, File
from sqlalchemy.orm import Session

from app.crud.firmware import firmware_crud, upgrade_task_crud
from app.db.session import get_db
from app.schemas.firmware import (
    Firmware, FirmwareCreate, FirmwareUpdate, FirmwareListResponse,
    FirmwareUpgradeTask, FirmwareUpgradeTaskCreate
)
from app.core.config import settings
from app.tasks.firmware_tasks import execute_firmware_upgrade

router = APIRouter()


# 简化的token验证（实际应通过gRPC调用auth-service）
def verify_token(authorization: str = Header(None)) -> dict:
    """验证JWT Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证信息")
    # 实际应通过gRPC调用auth-service验证
    return {"user_id": 1, "username": "admin"}


@router.get("/", response_model=FirmwareListResponse)
def list_firmware(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取固件列表"""
    skip = (page - 1) * page_size
    firmwares, total = firmware_crud.get_multi(
        db, skip=skip, limit=page_size,
        product_id=product_id, is_active=is_active
    )
    return FirmwareListResponse(
        firmwares=firmwares,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/upload", response_model=Firmware)
async def upload_firmware(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    version: str = Query(...),
    product_id: str = Query(...),
    description: Optional[str] = Query(None),
    release_notes: Optional[str] = Query(None),
    is_beta: bool = Query(False),
    min_hardware_version: Optional[str] = Query(None),
    current_user: dict = Depends(verify_token),
) -> Any:
    """上传固件文件"""
    # 检查版本是否已存在
    existing = firmware_crud.get_by_version(db, version)
    if existing:
        raise HTTPException(status_code=400, detail="该版本固件已存在")

    # 保存文件
    file_name = f"{product_id}_{version}_{file.filename}"
    file_path = os.path.join(settings.FIRMWARE_UPLOAD_DIR, file_name)

    # 计算文件哈希并保存
    file_content = await file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()
    file_size = len(file_content)

    with open(file_path, "wb") as f:
        f.write(file_content)

    # 创建固件记录
    firmware_data = FirmwareCreate(
        version=version,
        product_id=product_id,
        file_name=file_name,
        file_path=file_path,
        file_url=f"{settings.FIRMWARE_BASE_URL}/{file_name}",
        file_size=file_size,
        file_hash=file_hash,
        description=description,
        release_notes=release_notes,
        is_beta=is_beta,
        min_hardware_version=min_hardware_version
    )

    firmware = firmware_crud.create(db, obj_in=firmware_data, created_by=current_user["user_id"])
    return firmware


@router.get("/{firmware_id}", response_model=Firmware)
def get_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取固件详情"""
    firmware = firmware_crud.get(db, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")
    return firmware


@router.put("/{firmware_id}", response_model=Firmware)
def update_firmware(
    firmware_id: int,
    *,
    db: Session = Depends(get_db),
    firmware_in: FirmwareUpdate,
    current_user: dict = Depends(verify_token),
) -> Any:
    """更新固件信息"""
    firmware = firmware_crud.get(db, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")

    firmware = firmware_crud.update(db, db_obj=firmware, obj_in=firmware_in)
    return firmware


@router.delete("/{firmware_id}")
def delete_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """删除固件"""
    firmware = firmware_crud.get(db, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")

    # 删除文件
    if os.path.exists(firmware.file_path):
        os.remove(firmware.file_path)

    firmware_crud.delete(db, firmware_id=firmware_id)
    return {"message": "固件已删除"}


@router.get("/latest/{product_id}", response_model=Firmware)
def get_latest_firmware(
    product_id: str,
    include_beta: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取指定产品的最新固件"""
    firmware = firmware_crud.get_latest(db, product_id, is_beta=include_beta)
    if not firmware:
        raise HTTPException(status_code=404, detail="未找到可用固件")
    return firmware


@router.post("/upgrade", response_model=FirmwareUpgradeTask)
def create_upgrade_task(
    *,
    db: Session = Depends(get_db),
    device_id: int = Query(...),
    device_identifier: str = Query(...),
    firmware_id: int = Query(...),
    current_user: dict = Depends(verify_token),
) -> Any:
    """创建固件升级任务"""
    # 检查固件是否存在
    firmware = firmware_crud.get(db, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="固件不存在")
    if not firmware.is_active:
        raise HTTPException(status_code=400, detail="固件已被禁用")

    # 创建升级任务
    task_data = FirmwareUpgradeTaskCreate(
        device_id=device_id,
        device_identifier=device_identifier,
        firmware_id=firmware_id
    )
    task = upgrade_task_crud.create(db, obj_in=task_data, created_by=current_user["user_id"])

    # 异步执行升级任务
    celery_task = execute_firmware_upgrade.delay(task.id)
    upgrade_task_crud.set_celery_task_id(db, task.id, celery_task.id)

    return task


@router.get("/tasks/", response_model=List[FirmwareUpgradeTask])
def list_upgrade_tasks(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_identifier: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取升级任务列表"""
    skip = (page - 1) * page_size
    tasks, _ = upgrade_task_crud.get_multi(
        db, skip=skip, limit=page_size,
        device_identifier=device_identifier, status=status
    )
    return tasks


@router.get("/tasks/{task_id}", response_model=FirmwareUpgradeTask)
def get_upgrade_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取升级任务详情"""
    task = upgrade_task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
