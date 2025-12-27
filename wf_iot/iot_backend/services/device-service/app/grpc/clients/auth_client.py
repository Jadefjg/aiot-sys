# Auth Service gRPC客户端

import grpc
import logging
import sys
import os

# 添加proto生成代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../proto/generated'))

from auth_pb2 import (
    ValidateTokenRequest, CheckPermissionRequest, GetUserByIdRequest
)
import auth_pb2_grpc

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthGrpcClient:
    """Auth Service gRPC客户端"""

    def __init__(self):
        self.channel = None
        self.stub = None

    def connect(self):
        """建立gRPC连接"""
        try:
            self.channel = grpc.insecure_channel(settings.AUTH_SERVICE_GRPC)
            self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)
            logger.info(f"Connected to Auth Service at {settings.AUTH_SERVICE_GRPC}")
        except Exception as e:
            logger.error(f"Failed to connect to Auth Service: {e}")

    def close(self):
        """关闭gRPC连接"""
        if self.channel:
            self.channel.close()
            logger.info("Disconnected from Auth Service")

    def validate_token(self, token: str) -> tuple[bool, int, str, str]:
        """
        验证JWT Token
        返回: (是否有效, 用户ID, 用户名, 错误信息)
        """
        if not self.stub:
            return False, 0, "", "Auth Service not connected"

        try:
            request = ValidateTokenRequest(token=token)
            response = self.stub.ValidateToken(request)
            return response.valid, response.user_id, response.username, response.error_message
        except grpc.RpcError as e:
            logger.error(f"gRPC error validating token: {e}")
            return False, 0, "", str(e)

    def check_permission(self, user_id: int, resource: str, action: str) -> tuple[bool, str]:
        """
        检查用户权限
        返回: (是否允许, 原因)
        """
        if not self.stub:
            return False, "Auth Service not connected"

        try:
            request = CheckPermissionRequest(
                user_id=user_id,
                resource=resource,
                action=action
            )
            response = self.stub.CheckPermission(request)
            return response.allowed, response.reason
        except grpc.RpcError as e:
            logger.error(f"gRPC error checking permission: {e}")
            return False, str(e)

    def get_user_by_id(self, user_id: int) -> dict:
        """获取用户信息"""
        if not self.stub:
            return None

        try:
            request = GetUserByIdRequest(user_id=user_id)
            response = self.stub.GetUserById(request)
            return {
                "id": response.id,
                "username": response.username,
                "email": response.email,
                "full_name": response.full_name,
                "is_active": response.is_active,
                "is_superuser": response.is_superuser
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting user: {e}")
            return None


# 全局客户端实例
auth_grpc_client = AuthGrpcClient()
