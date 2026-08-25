"""系统模块配置 API（setting/:module）"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_active_superuser, get_current_active_user
from app.schemas.user import User
from app.services import settings_store

router = APIRouter()


@router.get("/")
def list_setting_modules(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return [{"module": m, "title": _module_title(m)} for m in settings_store.list_modules()]


@router.get("/{module}/form")
def get_setting_form(
    module: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    try:
        return {"module": module, "fields": settings_store.get_form(module)}
    except KeyError:
        raise HTTPException(status_code=404, detail="未知配置模块")


@router.get("/{module}")
def get_setting_values(
    module: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    try:
        return {"module": module, "values": settings_store.get_values(module)}
    except KeyError:
        raise HTTPException(status_code=404, detail="未知配置模块")


@router.post("/{module}")
def save_setting_values(
    module: str,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    try:
        values = settings_store.save_values(module, body)
        return {"module": module, "values": values, "message": "保存成功"}
    except KeyError:
        raise HTTPException(status_code=404, detail="未知配置模块")


def _module_title(module: str) -> str:
    titles = {
        "log": "日志",
        "mqtt": "MQTT 客户端",
        "web": "Web 服务",
        "broker": "内置 Broker",
        "oem": "品牌 OEM",
        "database": "数据库",
    }
    return titles.get(module, module)
