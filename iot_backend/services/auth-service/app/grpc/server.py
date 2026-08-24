# Auth Service gRPC服务端实现

import grpc
from concurrent import futures
import sys
import os

# 添加proto生成代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../proto/generated'))

from auth_pb2 import (
    ValidateTokenResponse, CheckPermissionResponse, UserResponse,
    PermissionListResponse, VerifyCredentialsResponse, RoleInfo, PermissionInfo
)
import auth_pb2_grpc

from app.db.session import SessionLocal
from app.crud.user import user_crud, role_crud, permission_crud
from app.core.security import validate_token, create_access_token, verify_password
from app.core.config import settings


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    """Auth Service gRPC服务实现"""

    def ValidateToken(self, request, context):
        """验证JWT Token"""
        token = request.token
        is_valid, username, error_msg = validate_token(token)

        if not is_valid:
            return ValidateTokenResponse(
                valid=False,
                error_message=error_msg or "Token无效"
            )

        # 获取用户信息
        db = SessionLocal()
        try:
            user = user_crud.get_by_username(db, username)
            if not user:
                return ValidateTokenResponse(
                    valid=False,
                    error_message="用户不存在"
                )
            if not user.is_active:
                return ValidateTokenResponse(
                    valid=False,
                    error_message="用户已被禁用"
                )
            return ValidateTokenResponse(
                valid=True,
                user_id=user.id,
                username=user.username
            )
        finally:
            db.close()

    def CheckPermission(self, request, context):
        """检查用户权限"""
        user_id = request.user_id
        resource = request.resource
        action = request.action

        db = SessionLocal()
        try:
            # 检查用户是否存在
            user = user_crud.get(db, user_id)
            if not user:
                return CheckPermissionResponse(
                    allowed=False,
                    reason="用户不存在"
                )

            # 超级用户拥有所有权限
            if user.is_supperuser:
                return CheckPermissionResponse(
                    allowed=True,
                    reason="超级用户"
                )

            # 检查权限
            has_perm = user_crud.has_permission(db, user_id, resource, action)
            if has_perm:
                return CheckPermissionResponse(
                    allowed=True,
                    reason="权限验证通过"
                )
            else:
                return CheckPermissionResponse(
                    allowed=False,
                    reason=f"缺少权限: {resource}:{action}"
                )
        finally:
            db.close()

    def GetUserById(self, request, context):
        """获取用户信息"""
        user_id = request.user_id

        db = SessionLocal()
        try:
            user = user_crud.get(db, user_id)
            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return UserResponse()

            # 获取用户角色
            roles = user_crud.get_user_roles(db, user_id)
            role_infos = [
                RoleInfo(id=role.id, name=role.name, description=role.description or "")
                for role in roles
            ]

            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email or "",
                full_name=user.full_name or "",
                is_active=user.is_active,
                is_superuser=user.is_supperuser,
                created_at=user.created_at.isoformat() if user.created_at else "",
                roles=role_infos
            )
        finally:
            db.close()

    def GetUserPermissions(self, request, context):
        """获取用户权限列表"""
        user_id = request.user_id

        db = SessionLocal()
        try:
            user = user_crud.get(db, user_id)
            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("用户不存在")
                return PermissionListResponse()

            permissions = user_crud.get_user_permissions(db, user_id)
            permission_infos = [
                PermissionInfo(
                    id=perm.id,
                    name=perm.name,
                    resource=perm.resource,
                    action=perm.action,
                    description=perm.description or ""
                )
                for perm in permissions
            ]

            return PermissionListResponse(permissions=permission_infos)
        finally:
            db.close()

    def VerifyCredentials(self, request, context):
        """验证用户凭证并返回Token"""
        username = request.username
        password = request.password

        db = SessionLocal()
        try:
            user = user_crud.authenticate(db, username, password)
            if not user:
                return VerifyCredentialsResponse(
                    success=False,
                    error_message="用户名或密码错误"
                )

            if not user.is_active:
                return VerifyCredentialsResponse(
                    success=False,
                    error_message="用户已被禁用"
                )

            # 创建访问令牌
            access_token = create_access_token(data={"sub": user.username})

            return VerifyCredentialsResponse(
                success=True,
                user_id=user.id,
                access_token=access_token,
                token_type="bearer"
            )
        finally:
            db.close()


def serve_grpc():
    """启动gRPC服务"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    server.add_insecure_port(f'[::]:{settings.GRPC_PORT}')
    server.start()
    print(f"Auth Service gRPC服务启动在端口 {settings.GRPC_PORT}")
    return server
