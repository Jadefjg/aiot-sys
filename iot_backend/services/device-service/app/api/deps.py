"""设备服务鉴权依赖：gRPC 调用 auth-service"""
from fastapi import Header, HTTPException

from app.grpc.clients.auth_client import auth_grpc_client


def verify_token(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证信息")
    token = authorization.split(" ")[1]
    valid, user_id, username, error = auth_grpc_client.validate_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=error or "Token无效")
    return {"user_id": user_id, "username": username}


def require_permission(user_id: int, resource: str, action: str):
    allowed, reason = auth_grpc_client.check_permission(user_id, resource, action)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason or "权限不足")
