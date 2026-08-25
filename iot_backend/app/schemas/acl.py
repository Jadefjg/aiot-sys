"""ACL 请求/响应"""
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator

ROLES = ("viewer", "operator", "admin")


class AclGrant(BaseModel):
    user_id: int
    role: str = "viewer"

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        role = (v or "viewer").lower()
        if role not in ROLES:
            raise ValueError("role 须为 viewer / operator / admin")
        return role


class AclEntry(BaseModel):
    user_id: int
    username: Optional[str] = None
    role: str
    product_id: Optional[str] = None
    device_id: Optional[str] = None

    class Config:
        from_attributes = True


class AclList(BaseModel):
    my_role: Optional[str] = None
    items: List[AclEntry] = []


class AccessSnapshot(BaseModel):
    is_superuser: bool = False
    products: Dict[str, str] = {}
    devices: Dict[str, str] = {}


class UserOption(BaseModel):
    id: int
    username: str
