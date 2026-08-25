"""内置协议元数据 API"""
import json
import os
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_current_active_user
from app.schemas.user import User
from app.services.protocol_manager import protocol_manager

router = APIRouter()

_PROTOCOL_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "protocols"
)


def _load_protocol(name: str) -> dict:
    path = os.path.abspath(os.path.join(_PROTOCOL_DIR, f"{name}.json"))
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="协议不存在")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/list")
def list_protocols(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """协议库列表，runtime 标记当前进程已注册的采集实现"""
    runtime = {p.lower() for p in protocol_manager.get_supported_protocols()}
    runtime.update({"http", "tcp", "opcua", "s7", "iec104", "bacnet", "knx"})
    items = []
    base = os.path.abspath(_PROTOCOL_DIR)
    if os.path.isdir(base):
        for fname in sorted(os.listdir(base)):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(base, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", fname[:-5])
            items.append({
                "name": name,
                "title": data.get("title", fname),
                "description": data.get("description", ""),
                "version": data.get("version", ""),
                "transport": data.get("transport", ""),
                "implemented": bool(data.get("implemented")),
                "runtime": name.lower() in runtime,
            })
    return items


@router.get("/{name}")
def get_protocol(
    name: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """协议详情 JSON"""
    return _load_protocol(name)
