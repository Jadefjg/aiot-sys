# Auth服务gRPC客户端

import grpc
import logging
from typing import Optional, List

from app.core.config import settings

# 导入生成的gRPC代码
import sys
sys.path.insert(0, '/app/proto_generated')
from proto_generated import auth_pb2, auth_pb2_grpc

logger = logging.getLogger(__name__)


class AuthGrpcClient:
    """Auth服务gRPC客户端"""

    def __init__(self):
        self.channel = None
        self.stub = None
        self._connect()

    def _connect(self):
        """建立gRPC连接"""
        try:
            self.channel = grpc.insecure_channel(settings.AUTH_SERVICE_GRPC_ADDRESS)
            self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)
            logger.info(f"已连接到Auth服务: {settings.AUTH_SERVICE_GRPC_ADDRESS}")
        except Exception as e:
            logger.error(f"连接Auth服务失败: {e}")
            raise

    def validate_token(self, token: str) -> Optional[dict]:
        """验证JWT Token"""
        try:
            request = auth_pb2.ValidateTokenRequest(token=token)
            response = self.stub.ValidateToken(request, timeout=5.0)

            if response.valid:
                return {
                    "user_id": response.user_id,
                    "username": response.username,
                    "roles": list(response.roles)
                }
            return None
        except grpc.RpcError as e:
            logger.error(f"Token验证RPC错误: {e.code()} - {e.details()}")
            return None
        except Exception as e:
            logger.error(f"Token验证异常: {e}")
            return None

    def check_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户权限"""
        try:
            request = auth_pb2.CheckPermissionRequest(
                user_id=user_id,
                permission_code=permission_code
            )
            response = self.stub.CheckPermission(request, timeout=5.0)
            return response.has_permission
        except grpc.RpcError as e:
            logger.error(f"权限检查RPC错误: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"权限检查异常: {e}")
            return False

    def close(self):
        """关闭gRPC连接"""
        if self.channel:
            self.channel.close()
            logger.info("Auth服务gRPC连接已关闭")


# 全局客户端实例
_auth_client: Optional[AuthGrpcClient] = None


def get_auth_client() -> AuthGrpcClient:
    """获取Auth gRPC客户端实例"""
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthGrpcClient()
    return _auth_client


def close_auth_client():
    """关闭Auth gRPC客户端"""
    global _auth_client
    if _auth_client:
        _auth_client.close()
        _auth_client = None
