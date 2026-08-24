"""告警 API"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission, verify_token
from app.crud.alarm import alarm_crud
from app.crud.device import device_crud
from app.db.session import get_db
from app.schemas.alarm import Alarm

router = APIRouter()


@router.get("/", response_model=List[Alarm])
def list_alarms(
    skip: int = 0,
    limit: int = 100,
    device_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    db_device_id = None
    if device_id:
        device = device_crud.get_by_device_id(db, device_id)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        db_device_id = device.id
    return alarm_crud.get_multi(
        db, skip=skip, limit=limit, device_id=db_device_id, acknowledged=acknowledged
    )


@router.post("/{alarm_id}/acknowledge", response_model=Alarm)
def acknowledge_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    alarm = alarm_crud.get(db, alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="告警不存在")
    return alarm_crud.acknowledge(db, alarm, current_user["user_id"])
