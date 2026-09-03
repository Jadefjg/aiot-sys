"""设备媒体上传与列表（不改动既有控制接口）"""
from typing import Any, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.media import media_crud
from app.db.session import get_db
from app.schemas.media import DeviceMediaOut
from app.schemas.user import User
from app.services import access_control as access
from app.services.media_service import save_upload

router = APIRouter()


@router.get("/{device_id}/media", response_model=List[DeviceMediaOut])
def list_device_media(
    device_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access.load_device(db, current_user, device_id, "viewer")
    return media_crud.list_by_device(db, device_id, limit=min(limit, 200))


@router.post("/{device_id}/media", response_model=DeviceMediaOut)
async def upload_device_media(
    device_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access.load_device(db, current_user, device_id, "operator")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件超过 20MB")
    return save_upload(db, device_id, file.filename or "file.bin", raw, file.content_type or "application/octet-stream")
