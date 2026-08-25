"""连接器 API：CRUD + 打开/关闭（进程内插件，避免 MQTT 回环双开）"""
import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, has_permission
from app.crud.link import link_crud
from app.db.session import get_db
from app.schemas.link import Link, LinkCreate, LinkOpenBody, LinkUpdate
from app.schemas.user import User
from app.services.link_devices import bound_devices_for_link

router = APIRouter()


def _dispatch_open(obj, options: dict, proto_payload: str) -> None:
    from app.services.dlt645_plugin import dlt645_plugin
    from app.services.link_bus_service import link_bus_service
    from app.services.modbus_plugin import modbus_plugin

    link_bus_service.on_link_message(
        f"link/{obj.linker}/{obj.link_id}/open", json.dumps(options).encode()
    )
    protocol = (obj.protocol or "modbus").lower()
    topic = f"protocol/{protocol}/{obj.linker}/{obj.link_id}/open"
    if protocol == "dlt645":
        dlt645_plugin.on_protocol(topic, proto_payload.encode())
    else:
        modbus_plugin.on_protocol(topic, proto_payload.encode())


def _dispatch_close(obj) -> None:
    from app.services.dlt645_plugin import dlt645_plugin
    from app.services.link_bus_service import link_bus_service
    from app.services.modbus_plugin import modbus_plugin

    protocol = (obj.protocol or "modbus").lower()
    topic = f"protocol/{protocol}/{obj.linker}/{obj.link_id}/close"
    if protocol == "dlt645":
        dlt645_plugin.on_protocol(topic, b"{}")
    else:
        modbus_plugin.on_protocol(topic, b"{}")
    link_bus_service.on_link_message(f"link/{obj.linker}/{obj.link_id}/close", b"{}")


@router.get("/", response_model=List[Link])
def list_links(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return link_crud.get_multi(db, skip=skip, limit=limit, gateway_id=gateway_id)


@router.post("/", response_model=Link, status_code=status.HTTP_201_CREATED)
def create_link(
    body: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("link:write")),
) -> Any:
    if link_crud.get_by_link_id(db, body.link_id):
        raise HTTPException(status_code=400, detail="连接 ID 已存在")
    return link_crud.create(db, body)


@router.put("/{link_id}", response_model=Link)
def update_link(
    link_id: str,
    body: LinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("link:write")),
) -> Any:
    obj = link_crud.get_by_link_id(db, link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="连接不存在")
    return link_crud.update(db, obj, body)


@router.delete("/{link_id}", response_model=Link)
def delete_link(
    link_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("link:write")),
) -> Any:
    obj = link_crud.get_by_link_id(db, link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="连接不存在")
    _dispatch_close(obj)
    return link_crud.delete(db, obj.id)


@router.post("/{link_id}/open", response_model=Link)
def open_link(
    link_id: str,
    body: Optional[LinkOpenBody] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("link:write")),
) -> Any:
    """打开连接并绑定协议插件设备列表"""
    obj = link_crud.get_by_link_id(db, link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="连接不存在")
    options = dict(obj.options or {})
    devices = (body.devices if body and body.devices else None) or bound_devices_for_link(db, link_id)
    proto_payload = json.dumps({"devices": devices, "poll_interval": options.get("poll_interval", 1000)})
    _dispatch_open(obj, options, proto_payload)
    db.expire_all()
    return link_crud.get_by_link_id(db, link_id) or obj


@router.post("/{link_id}/close", response_model=Link)
def close_link(
    link_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("link:write")),
) -> Any:
    obj = link_crud.get_by_link_id(db, link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="连接不存在")
    _dispatch_close(obj)
    db.expire_all()
    return link_crud.get_by_link_id(db, link_id) or obj
