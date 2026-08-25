"""DGIoT 数据通道 API：采集/资源通道 CRUD、启停、日志、HTTP 采集入口"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, has_permission
from app.crud.channel import channel_crud
from app.db.session import get_db
from app.schemas.channel import Channel, ChannelCreate, ChannelIngest, ChannelLog, ChannelUpdate
from app.schemas.user import User
from app.services.channel_runtime import channel_runtime
from app.services.device_runtime_service import device_runtime
from app.services.mqtt_service import mqtt_client

router = APIRouter()


@router.get("/", response_model=List[Channel])
def list_channels(
    skip: int = 0,
    limit: int = 100,
    kind: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return channel_crud.get_multi(db, skip=skip, limit=limit, kind=kind)


@router.post("/", response_model=Channel, status_code=status.HTTP_201_CREATED)
def create_channel(
    body: ChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("channel:write")),
) -> Any:
    if channel_crud.get_by_channel_id(db, body.channel_id):
        raise HTTPException(status_code=400, detail="通道 ID 已存在")
    if body.kind not in ("collect", "resource"):
        raise HTTPException(status_code=400, detail="kind 须为 collect 或 resource")
    obj = channel_crud.create(db, body)
    channel_runtime.invalidate()
    return obj


@router.put("/{channel_id}", response_model=Channel)
def update_channel(
    channel_id: str,
    body: ChannelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("channel:write")),
) -> Any:
    obj = channel_crud.get_by_channel_id(db, channel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="通道不存在")
    updated = channel_crud.update(db, obj, body)
    channel_runtime.invalidate()
    return updated


@router.delete("/{channel_id}", response_model=Channel)
def delete_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("channel:write")),
) -> Any:
    obj = channel_crud.get_by_channel_id(db, channel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="通道不存在")
    deleted = channel_crud.delete(db, obj.id)
    channel_runtime.invalidate()
    return deleted


@router.post("/{channel_id}/enable", response_model=Channel)
def enable_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("channel:write")),
) -> Any:
    obj = channel_crud.get_by_channel_id(db, channel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="通道不存在")
    status_name = "running"
    if obj.kind == "collect":
        status_name = channel_runtime.start_collect(db, obj)
    obj = channel_crud.update(db, obj, ChannelUpdate(enabled=True, status=status_name))
    channel_runtime.invalidate()
    return obj


@router.post("/{channel_id}/disable", response_model=Channel)
def disable_channel(
    channel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("channel:write")),
) -> Any:
    obj = channel_crud.get_by_channel_id(db, channel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="通道不存在")
    if obj.kind == "collect":
        channel_runtime.stop_collect(db, obj)
    obj = channel_crud.update(db, obj, ChannelUpdate(enabled=False, status="stopped"))
    channel_runtime.invalidate()
    return obj


@router.get("/{channel_id}/logs", response_model=List[ChannelLog])
def channel_logs(
    channel_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not channel_crud.get_by_channel_id(db, channel_id):
        raise HTTPException(status_code=404, detail="通道不存在")
    return channel_crud.list_logs(db, channel_id, limit=limit)


@router.post("/{channel_id}/ingest")
def ingest_http(
    channel_id: str,
    body: ChannelIngest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """HTTP 采集通道入口，对齐 DGIoT HTTP 设备上报"""
    obj = channel_crud.get_by_channel_id(db, channel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="通道不存在")
    if not obj.enabled:
        raise HTTPException(status_code=400, detail="通道未启用")
    payload = dict(body.values or {})
    if isinstance(body.raw, dict):
        payload.update(body.raw)
    elif body.raw is not None:
        payload["raw"] = body.raw
    if not payload:
        raise HTTPException(status_code=400, detail="values 或 raw 至少提供一项")
    device = device_runtime.put_values(
        db, body.device_id, payload, publish_alarm=mqtt_client._publish_alarm
    )
    channel_crud.add_log(db, channel_id, f"ingest {body.device_id}", payload=payload)
    return {"device_id": body.device_id, "values": device.values if device else payload}
