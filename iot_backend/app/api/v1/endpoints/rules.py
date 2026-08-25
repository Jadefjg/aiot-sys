"""规则引擎与设备影子 API"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, has_permission
from app.crud.channel import rule_crud, shadow_crud
from app.db.session import get_db
from app.schemas.channel import (
    DataRule, DataRuleCreate, DataRuleUpdate, DeviceShadow, ShadowDesired,
)
from app.schemas.user import User
from app.services import access_control as access
from app.services.device_runtime_service import device_runtime
from app.services.mqtt_service import mqtt_client
import json
import uuid

rules_router = APIRouter()
shadow_router = APIRouter()


@rules_router.get("/", response_model=List[DataRule])
def list_rules(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    rows = rule_crud.get_multi(db, skip=0, limit=500)
    if not current_user.is_superuser:
        allowed = set(access.visible_product_ids(db, current_user))
        rows = [r for r in rows if not r.product_id or r.product_id in allowed]
    return rows[skip:skip + limit]


def _ensure_rule_action_targets(db: Session, user: User, actions) -> None:
    """校验规则动作中的写设备目标 ACL"""
    for action in actions or []:
        if not isinstance(action, dict):
            continue
        if action.get("type") == "write" and action.get("device_id"):
            access.load_device(db, user, action["device_id"], "operator")


@rules_router.post("/", response_model=DataRule, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: DataRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("rule:write")),
) -> Any:
    if body.product_id:
        access.ensure_product(db, current_user, body.product_id, "operator")
    elif not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="全局规则仅超级管理员可创建")
    if body.device_id:
        access.load_device(db, current_user, body.device_id, "operator")
    _ensure_rule_action_targets(db, current_user, body.actions)
    from app.services.rule_engine import rule_engine
    obj = rule_crud.create(db, body)
    rule_engine.invalidate()
    return obj


@rules_router.put("/{rule_id}", response_model=DataRule)
def update_rule(
    rule_id: int,
    body: DataRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("rule:write")),
) -> Any:
    obj = rule_crud.get(db, rule_id)
    if not obj:
        raise HTTPException(status_code=404, detail="规则不存在")
    if obj.product_id:
        access.ensure_product(db, current_user, obj.product_id, "operator")
    elif not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="全局规则仅超级管理员可修改")
    product_id = body.product_id if body.product_id is not None else obj.product_id
    if product_id:
        access.ensure_product(db, current_user, product_id, "operator")
    device_id = body.device_id if body.device_id is not None else obj.device_id
    if device_id:
        access.load_device(db, current_user, device_id, "operator")
    actions = body.actions if body.actions is not None else obj.actions
    _ensure_rule_action_targets(db, current_user, actions)
    from app.services.rule_engine import rule_engine
    updated = rule_crud.update(db, obj, body)
    rule_engine.invalidate()
    return updated


@rules_router.delete("/{rule_id}", response_model=DataRule)
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(has_permission("rule:write")),
) -> Any:
    obj = rule_crud.get(db, rule_id)
    if not obj:
        raise HTTPException(status_code=404, detail="规则不存在")
    if obj.product_id:
        access.ensure_product(db, current_user, obj.product_id, "operator")
    elif not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="全局规则仅超级管理员可删除")
    obj = rule_crud.delete(db, rule_id)
    from app.services.rule_engine import rule_engine
    rule_engine.invalidate()
    return obj


@shadow_router.get("/{device_id}/shadow", response_model=DeviceShadow)
def get_shadow(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access.load_device(db, current_user, device_id, "viewer")
    obj = shadow_crud.get(db, device_id)
    if not obj:
        return DeviceShadow(device_id=device_id, reported={}, desired={}, version=0)
    return obj


@shadow_router.put("/{device_id}/shadow", response_model=DeviceShadow)
def set_shadow_desired(
    device_id: str,
    body: ShadowDesired,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """更新期望状态并经 MQTT setting 下发"""
    device = access.load_device(db, current_user, device_id, "operator")
    obj = shadow_crud.set_desired(db, device_id, body.desired)
    payload = {
        "msg_id": str(uuid.uuid4()),
        "device_id": device_id,
        "name": "shadow",
        "data": body.desired,
    }
    mqtt_client.publish(device_runtime._target_topic(device, "setting"), json.dumps(payload))
    return obj
