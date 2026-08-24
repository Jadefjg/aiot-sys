# MQTT Gateway gRPC客户端

import grpc
import logging
import json
from typing import Optional

from app.core.config import settings

# 导入生成的gRPC代码
import sys
sys.path.insert(0, '/app/proto_generated')
from proto_generated import mqtt_gateway_pb2, mqtt_gateway_pb2_grpc

logger = logging.getLogger(__name__)


class MqttGrpcClient:
    """MQTT Gateway gRPC客户端"""

    def __init__(self):
        self.channel = None
        self.stub = None
        self._connect()

    def _connect(self):
        """建立gRPC连接"""
        try:
            self.channel = grpc.insecure_channel(settings.MQTT_GATEWAY_GRPC_ADDRESS)
            self.stub = mqtt_gateway_pb2_grpc.MqttGatewayServiceStub(self.channel)
            logger.info(f"已连接到MQTT Gateway: {settings.MQTT_GATEWAY_GRPC_ADDRESS}")
        except Exception as e:
            logger.error(f"连接MQTT Gateway失败: {e}")
            raise

    def send_firmware_upgrade_command(
        self,
        device_identifier: str,
        firmware_id: int,
        firmware_version: str,
        download_url: str,
        file_hash: str,
        file_size: int
    ) -> bool:
        """发送固件升级命令到设备"""
        try:
            # 构建升级命令payload
            payload = json.dumps({
                "action": "firmware_upgrade",
                "firmware_id": firmware_id,
                "version": firmware_version,
                "download_url": download_url,
                "file_hash": file_hash,
                "file_size": file_size
            })

            topic = f"device/{device_identifier}/firmware"

            request = mqtt_gateway_pb2.PublishRequest(
                topic=topic,
                payload=payload,
                qos=1,  # 至少一次传递
                retain=False
            )
            response = self.stub.Publish(request, timeout=10.0)

            if response.success:
                logger.info(f"已发送固件升级命令到设备 {device_identifier}")
                return True
            else:
                logger.error(f"发送固件升级命令失败: {response.message}")
                return False

        except grpc.RpcError as e:
            logger.error(f"发送升级命令RPC错误: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"发送升级命令异常: {e}")
            return False

    def publish_message(self, topic: str, payload: str, qos: int = 0) -> bool:
        """发布MQTT消息"""
        try:
            request = mqtt_gateway_pb2.PublishRequest(
                topic=topic,
                payload=payload,
                qos=qos,
                retain=False
            )
            response = self.stub.Publish(request, timeout=5.0)
            return response.success
        except grpc.RpcError as e:
            logger.error(f"发布消息RPC错误: {e.code()} - {e.details()}")
            return False
        except Exception as e:
            logger.error(f"发布消息异常: {e}")
            return False

    def close(self):
        """关闭gRPC连接"""
        if self.channel:
            self.channel.close()
            logger.info("MQTT Gateway gRPC连接已关闭")


# 全局客户端实例
_mqtt_client: Optional[MqttGrpcClient] = None


def get_mqtt_client() -> MqttGrpcClient:
    """获取MQTT gRPC客户端实例"""
    global _mqtt_client
    if _mqtt_client is None:
        _mqtt_client = MqttGrpcClient()
    return _mqtt_client


def close_mqtt_client():
    """关闭MQTT gRPC客户端"""
    global _mqtt_client
    if _mqtt_client:
        _mqtt_client.close()
        _mqtt_client = None
