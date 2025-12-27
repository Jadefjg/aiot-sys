# Token Schema

from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT令牌响应模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None
