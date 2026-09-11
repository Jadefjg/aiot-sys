# 认证与授权(JWT)

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_password_material(plain_password), hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(_password_material(password))

def _password_material(password: str) -> str:
    value = str(password or "")
    if len(value.encode("utf-8")) > 72:
        return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
    return value

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now()
    # iat/jti enable downstream services to audit tokens and support revocation.
    to_encode.update({"exp": expire, "iat": now, "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
