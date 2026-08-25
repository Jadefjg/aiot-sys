"""系统模块配置读写（对标 note02 setting/:module）"""
import json
import os
from typing import Any, Dict, List

from app.core.config import settings

# 各模块表单定义
MODULE_FORMS: Dict[str, List[Dict[str, Any]]] = {
    "log": [
        {"name": "level", "label": "日志级别", "type": "select", "options": ["DEBUG", "INFO", "WARNING", "ERROR"]},
        {"name": "file_path", "label": "日志路径", "type": "text"},
        {"name": "max_size_mb", "label": "单文件上限(MB)", "type": "number"},
    ],
    "mqtt": [
        {"name": "host", "label": "Broker 地址", "type": "text"},
        {"name": "port", "label": "端口", "type": "number"},
        {"name": "username", "label": "用户名", "type": "text"},
        {"name": "password", "label": "密码", "type": "password"},
    ],
    "web": [
        {"name": "project_name", "label": "项目名称", "type": "text"},
        {"name": "access_token_expire_minutes", "label": "JWT 过期(分钟)", "type": "number"},
        {"name": "cors_origins", "label": "CORS 来源", "type": "text"},
    ],
    "broker": [
        {"name": "enabled", "label": "启用内置 Broker", "type": "switch"},
        {"name": "port", "label": "监听端口", "type": "number"},
        {"name": "ws_port", "label": "WebSocket 端口", "type": "number"},
    ],
    "oem": [
        {"name": "brand_name", "label": "品牌名称", "type": "text"},
        {"name": "logo_url", "label": "Logo URL", "type": "text"},
        {"name": "copyright", "label": "版权信息", "type": "text"},
    ],
    "database": [
        {"name": "host", "label": "MySQL 主机", "type": "text"},
        {"name": "port", "label": "端口", "type": "number"},
        {"name": "user", "label": "用户名", "type": "text"},
        {"name": "database", "label": "库名", "type": "text"},
    ],
}

_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "runtime_settings.json")


def _defaults(module: str) -> Dict[str, Any]:
    """从环境配置生成默认值"""
    if module == "log":
        return {"level": "INFO", "file_path": "/var/log/iot/app.log", "max_size_mb": 100}
    if module == "mqtt":
        return {
            "host": settings.MQTT_BROKER_HOST,
            "port": settings.MQTT_BROKER_PORT,
            "username": settings.MQTT_USERNAME or "",
            "password": "",
        }
    if module == "web":
        return {
            "project_name": settings.PROJECT_NAME,
            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "cors_origins": settings.CORS_ORIGINS,
        }
    if module == "broker":
        return {"enabled": True, "port": 1883, "ws_port": 8083}
    if module == "oem":
        return {"brand_name": "IoT管理系统", "logo_url": "", "copyright": ""}
    if module == "database":
        return {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "user": settings.MYSQL_USER,
            "database": settings.MYSQL_DATABASE,
        }
    return {}


def _load_store() -> Dict[str, Any]:
    path = os.path.abspath(_STORE_PATH)
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(data: Dict[str, Any]) -> None:
    path = os.path.abspath(_STORE_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_modules() -> List[str]:
    return list(MODULE_FORMS.keys())


def get_form(module: str) -> List[Dict[str, Any]]:
    if module not in MODULE_FORMS:
        raise KeyError(module)
    return MODULE_FORMS[module]


_SECRET_KEYS = {"password", "secret", "token", "access_key"}


def get_values(module: str, redact: bool = True) -> Dict[str, Any]:
    if module not in MODULE_FORMS:
        raise KeyError(module)
    stored = _load_store().get(module, {})
    values = {**_defaults(module), **stored}
    if redact:
        for key, val in list(values.items()):
            if key.lower() in _SECRET_KEYS and val:
                values[key] = "******"
    return values


def save_values(module: str, values: Dict[str, Any]) -> Dict[str, Any]:
    if module not in MODULE_FORMS:
        raise KeyError(module)
    all_data = _load_store()
    current = {**_defaults(module), **all_data.get(module, {})}
    incoming = dict(values or {})
    for key, val in list(incoming.items()):
        if key.lower() in _SECRET_KEYS and val in ("", "******"):
            incoming.pop(key, None)
    merged = {**current, **incoming}
    all_data[module] = merged
    _save_store(all_data)
    return get_values(module, redact=True)
