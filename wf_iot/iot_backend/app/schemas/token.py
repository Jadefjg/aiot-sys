from pydantic import BaseModel


class Token(BaseModel):
    """JWT令牌响应模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    username: str | None = None
