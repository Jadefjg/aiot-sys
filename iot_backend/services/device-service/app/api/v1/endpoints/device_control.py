"""设备远程控制（经 mqtt-gateway + Redis 响应队列）"""
import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission, verify_token
from app.crud.device import device_crud
from app.db.session import get_db
from app.grpc.clients.mqtt_client import mqtt_grpc_client
from app.schemas.device import (
    Device, DeviceActionRequest, DeviceReadRequest, DeviceRegisterRequest,
    DeviceSettingRequest, DeviceWriteRequest,
)
from app.services.control_bus import request_device
from app.services.device_runtime_service import device_runtime

router = APIRouter()


def _device(db: Session, device_id: str, user: dict, action: str = "read"):
    require_permission(user["user_id"], "device", action)
    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


def _call(device, action: str, payload: dict) -> dict:
    try:
        return request_device(device, action, payload)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))


def _publish_alarm(device_id: str, alarm: dict):
    mqtt_grpc_client.publish_message(
        f"device/{device_id}/alarm", json.dumps(alarm, ensure_ascii=False)
    )


@router.post("/{device_id}/register", response_model=Device)
def register_device(
    device_id: str,
    body: Optional[DeviceRegisterRequest] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    body = body or DeviceRegisterRequest()
    return device_runtime.register(
        db, device_id, body.product_id, body.device_name, body.gateway_id
    )


@router.get("/{device_id}/values")
def get_device_values(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user)
    return {"device_id": device_id, "values": device.values or {}, "status": device.status}


@router.post("/{device_id}/values")
def put_device_values(
    device_id: str,
    body: DeviceWriteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    _device(db, device_id, current_user, "write")
    device = device_runtime.put_values(db, device_id, body.values, _publish_alarm)
    return {"device_id": device_id, "values": device.values}


@router.get("/{device_id}/sync")
def sync_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user, "write")
    return {"device_id": device_id, "response": _call(device, "sync", {})}


@router.post("/{device_id}/read")
def read_device_points(
    device_id: str,
    body: DeviceReadRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user, "write")
    return {"device_id": device_id, "response": _call(device, "read", {"points": body.points})}


@router.post("/{device_id}/write")
def write_device_points(
    device_id: str,
    body: DeviceWriteRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user, "write")
    return {"device_id": device_id, "response": _call(device, "write", {"values": body.values})}


@router.post("/{device_id}/action/{action}")
def invoke_device_action(
    device_id: str,
    action: str,
    body: Optional[DeviceActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user, "write")
    body = body or DeviceActionRequest()
    resp = _call(device, "action", {"action": action, "params": body.params or {}})
    return {"device_id": device_id, "action": action, "response": resp}


@router.post("/{device_id}/setting/{name}")
def push_device_setting(
    device_id: str,
    name: str,
    body: DeviceSettingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    device = _device(db, device_id, current_user, "write")
    resp = _call(device, "setting", {"name": name, "data": body.data})
    return {"device_id": device_id, "setting": name, "response": resp}
