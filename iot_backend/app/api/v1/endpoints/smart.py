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

bindings_router = APIRouter()
scripts_router = APIRouter()


@bindings_router.get("/", response_model=List[Binding])
def list_bindings(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return binding_crud.get_multi(db, skip=skip, limit=limit, gateway_id=gateway_id)


@bindings_router.post("/", response_model=Binding, status_code=status.HTTP_201_CREATED)
def create_binding(
    body: BindingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
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
    obj = binding_crud.delete(db, binding_id)
    if not obj:
        raise HTTPException(status_code=404, detail="联动不存在")
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
    return script_crud.get_multi(db, skip=skip, limit=limit, gateway_id=gateway_id)


@scripts_router.post("/", response_model=Script, status_code=status.HTTP_201_CREATED)
def create_script(
    body: ScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
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
    from app.services.script_engine import script_engine
    body = body or {}
    return script_engine.run_content(
        obj.content,
        obj.language or "js",
        body.get("device_id") or obj.gateway_id or "",
        body.get("values") or {},
        apply=True,
    )


@scripts_router.post("/preview")
def preview_script(
    body: dict,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    from app.services.script_engine import script_engine
    return script_engine.run_content(
        body.get("content") or "",
        body.get("language") or "js",
        body.get("device_id") or "",
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
    obj = script_crud.delete(db, script_id)
    if not obj:
        raise HTTPException(status_code=404, detail="脚本不存在")
    from app.services.script_engine import script_engine
    script_engine.invalidate()
    return obj
