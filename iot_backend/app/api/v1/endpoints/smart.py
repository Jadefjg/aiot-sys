"""联动绑定与边缘脚本 API"""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.group import binding_crud, script_crud
from app.db.session import get_db
from app.schemas.link import (
    Binding, BindingCreate, BindingUpdate,
    Script, ScriptCreate, ScriptUpdate,
)
from app.schemas.user import User
from app.services import access_control as access

bindings_router = APIRouter()
scripts_router = APIRouter()


def _ensure_binding_write(db: Session, user: User, body) -> None:
    gateway_id = getattr(body, "gateway_id", None)
    if gateway_id:
        access.ensure_gateway(db, user, gateway_id, "operator")
    access.ensure_devices(
        db,
        user,
        [getattr(body, "device1_id", None), getattr(body, "device2_id", None)],
        "operator",
    )


@bindings_router.get("/", response_model=List[Binding])
def list_bindings(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if gateway_id and not current_user.is_superuser:
        access.load_device(db, current_user, gateway_id, "viewer")
    rows = binding_crud.get_multi(db, skip=0, limit=500, gateway_id=gateway_id)
    visible = access.visible_device_id_set(db, current_user)
    if visible is not None:
        rows = [
            r for r in rows
            if (not r.gateway_id or r.gateway_id in visible)
            and r.device1_id in visible
            and r.device2_id in visible
        ]
    return rows[skip:skip + limit]


@bindings_router.post("/", response_model=Binding, status_code=status.HTTP_201_CREATED)
def create_binding(
    body: BindingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    _ensure_binding_write(db, current_user, body)
    obj = binding_crud.create(db, body)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return obj


@bindings_router.put("/{binding_id}", response_model=Binding)
def update_binding(
    binding_id: int,
    body: BindingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    obj = binding_crud.get(db, binding_id)
    if not obj:
        raise HTTPException(status_code=404, detail="联动不存在")
    if obj.gateway_id:
        access.ensure_gateway(db, current_user, obj.gateway_id, "operator")
    access.ensure_devices(db, current_user, [obj.device1_id, obj.device2_id], "operator")
    merged_gateway = body.gateway_id if body.gateway_id is not None else obj.gateway_id
    merged_d1 = body.device1_id if body.device1_id is not None else obj.device1_id
    merged_d2 = body.device2_id if body.device2_id is not None else obj.device2_id

    class _Tmp:
        pass

    tmp = _Tmp()
    tmp.gateway_id = merged_gateway
    tmp.device1_id = merged_d1
    tmp.device2_id = merged_d2
    _ensure_binding_write(db, current_user, tmp)
    obj = binding_crud.update(db, obj, body)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return obj


@bindings_router.delete("/{binding_id}", response_model=Binding)
def delete_binding(
    binding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    obj = binding_crud.get(db, binding_id)
    if not obj:
        raise HTTPException(status_code=404, detail="联动不存在")
    if obj.gateway_id:
        access.ensure_gateway(db, current_user, obj.gateway_id, "operator")
    access.ensure_devices(db, current_user, [obj.device1_id, obj.device2_id], "operator")
    obj = binding_crud.delete(db, binding_id)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return obj


@scripts_router.get("/", response_model=List[Script])
def list_scripts(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if gateway_id and not current_user.is_superuser:
        access.load_device(db, current_user, gateway_id, "viewer")
    rows = script_crud.get_multi(db, skip=0, limit=500, gateway_id=gateway_id)
    rows = access.filter_by_gateway(rows, db, current_user)
    return rows[skip:skip + limit]


@scripts_router.post("/", response_model=Script, status_code=status.HTTP_201_CREATED)
def create_script(
    body: ScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access.ensure_gateway(db, current_user, body.gateway_id, "operator")
    obj = script_crud.create(db, body)
    from app.services.script_engine import script_engine
    script_engine.invalidate()
    return obj


@scripts_router.post("/{script_id}/run")
def run_script(
    script_id: int,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """立即执行边缘脚本（可用 device_id / values 注入）"""
    obj = script_crud.get(db, script_id)
    if not obj:
        raise HTTPException(status_code=404, detail="脚本不存在")
    access.ensure_gateway(db, current_user, obj.gateway_id, "operator")
    body = body or {}
    target = body.get("device_id") or obj.gateway_id or ""
    if target:
        access.load_device(db, current_user, target, "operator")
    from app.services.script_engine import script_engine
    result = script_engine.run_content(
        obj.content,
        obj.language or "js",
        target,
        body.get("values") or {},
        apply=False,
    )
    # 写目标需具备 operator，防止脚本越权写任意设备
    for item in result.get("writes") or []:
        write_id = item[0] if isinstance(item, (list, tuple)) else (item.get("device_id") if isinstance(item, dict) else None)
        if write_id:
            access.load_device(db, current_user, write_id, "operator")
    if result.get("writes"):
        script_engine.apply_writes(result["writes"])
    return result


@scripts_router.post("/preview")
def preview_script(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device_id = body.get("device_id") or ""
    if device_id:
        access.load_device(db, current_user, device_id, "viewer")
    from app.services.script_engine import script_engine
    return script_engine.run_content(
        body.get("content") or "",
        body.get("language") or "js",
        device_id,
        body.get("values") or {},
    )


@scripts_router.put("/{script_id}", response_model=Script)
def update_script(
    script_id: int,
    body: ScriptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    obj = script_crud.get(db, script_id)
    if not obj:
        raise HTTPException(status_code=404, detail="脚本不存在")
    access.ensure_gateway(db, current_user, obj.gateway_id, "operator")
    gateway_id = body.gateway_id if body.gateway_id is not None else obj.gateway_id
    access.ensure_gateway(db, current_user, gateway_id, "operator")
    obj = script_crud.update(db, obj, body)
    from app.services.script_engine import script_engine
    script_engine.invalidate()
    return obj


@scripts_router.delete("/{script_id}", response_model=Script)
def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    obj = script_crud.get(db, script_id)
    if not obj:
        raise HTTPException(status_code=404, detail="脚本不存在")
    access.ensure_gateway(db, current_user, obj.gateway_id, "operator")
    obj = script_crud.delete(db, script_id)
    from app.services.script_engine import script_engine
    script_engine.invalidate()
    return obj
