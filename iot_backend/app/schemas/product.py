"""产品与物模型 Schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ThingProperty(BaseModel):
    name: str
    label: Optional[str] = None
    unit: Optional[str] = None
    type: str = "number"  # number/string/boolean/enum
    mode: str = "r"  # r / w / rw
    precision: Optional[int] = None


class ThingEvent(BaseModel):
    name: str
    label: Optional[str] = None
    params: Optional[List[Dict[str, Any]]] = None


class ThingAction(BaseModel):
    name: str
    label: Optional[str] = None
    type: str = "button"  # button/switch/slider
    params: Optional[List[Dict[str, Any]]] = None


class ThingValidator(BaseModel):
    name: Optional[str] = None
    type: str = "compare"  # compare / expression
    field: Optional[str] = None
    operator: Optional[str] = None  # = != > >= < <=
    value: Optional[Any] = None
    expression: Optional[str] = None
    title: str = "告警"
    message: Optional[str] = None
    level: str = "warning"
    delay: int = 0
    reset: int = 0
    reset_times: int = 0


class ThingSetting(BaseModel):
    name: str
    label: Optional[str] = None
    type: str = "string"
    default: Optional[Any] = None


class ThingModel(BaseModel):
    properties: List[ThingProperty] = Field(default_factory=list)
    events: List[ThingEvent] = Field(default_factory=list)
    actions: List[ThingAction] = Field(default_factory=list)
    validators: List[ThingValidator] = Field(default_factory=list)
    settings: List[ThingSetting] = Field(default_factory=list)


class ProductBase(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    protocol: Optional[str] = None
    version: Optional[str] = None
    image_url: Optional[str] = None
    is_gateway: bool = False
    smart: bool = False
    controllable: bool = True
    writable: bool = True
    programmable: bool = False
    configurable: bool = False
    ota: bool = False
    locatable: bool = False
    model: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    protocol: Optional[str] = None
    version: Optional[str] = None
    image_url: Optional[str] = None
    is_gateway: Optional[bool] = None
    smart: Optional[bool] = None
    controllable: Optional[bool] = None
    writable: Optional[bool] = None
    programmable: Optional[bool] = None
    configurable: Optional[bool] = None
    ota: Optional[bool] = None
    locatable: Optional[bool] = None
    model: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
