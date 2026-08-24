# MQTT Gateway gRPC客户端

import grpc
import json
import logging
import sys
import os

# 添加proto生成代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../proto/generated'))

from google.protobuf import struct_pb2
from mqtt_gateway_pb2 import (
    PublishMessageRequest, SendDeviceCommandRequest, SendFirmwareUpgradeRequest,
    GetConnectionStatusRequest, GetDeviceOnlineStatusRequest
)
import mqtt_gateway_pb2_grpc

from app.core.config import settings

logger = logging.getLogger(__name__)


def dict_to_struct(d: dict) -> struct_pb2.Struct:
    """将Python字典转换为protobuf Struct"""
    struct = struct_pb2.Struct()
    struct.update(d)
    return struct


class MqttGrpcClient:
    """MQTT Gateway gRPC客户端"""

    def __init__(self):
        self.channel = None
        self.stub = None

    def connect(self):
        """建立gRPC连接"""
        try:
            self.channel = grpc.insecure_channel(settings.MQTT_GATEWAY_GRPC)
            self.stub = mqtt_gateway_pb2_grpc.MqttGatewayServiceStub(self.channel)
            logger.info(f"Connected to MQTT Gateway at {settings.MQTT_GATEWAY_GRPC}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT Gateway: {e}")

    def close(self):
        """关闭gRPC连接"""
        if self.channel:
            self.channel.close()
            logger.info("Disconnected from MQTT Gateway")

    def publish_message(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> tuple[bool, str]:
        """
        发布MQTT消息
        返回: (是否成功, 消息ID或错误信息)
        """
        if not self.stub:
            return False, "MQTT Gateway not connected"

        try:
            request = PublishMessageRequest(
                topic=topic,
                payload=payload.encode('utf-8'),
                qos=qos,
                retain=retain
            )
            response = self.stub.PublishMessage(request)
            if response.success:
                return True, response.message_id
            else:
                return False, response.error_message
        except grpc.RpcError as e:
            logger.error(f"gRPC error publishing message: {e}")
            return False, str(e)

    def send_device_command(
        self,
        device_id: str,
        command_type: str,
        command_data: dict,
        timeout_seconds: int = 30,
        qos: int = 1
    ) -> tuple[bool, str]:
        """
        发送设备命令
        返回: (是否成功, 命令ID或错误信息)
        """
        if not self.stub:
            return False, "MQTT Gateway not connected"

        try:
            request = SendDeviceCommandRequest(
                device_id=device_id,
                command_type=command_type,
                command_data=dict_to_struct(command_data),
                timeout_seconds=timeout_seconds,
                qos=qos
            )
            response = self.stub.SendDeviceCommand(request)
            if response.success:
                return True, response.command_id
            else:
                return False, response.error_message
        except grpc.RpcError as e:
            logger.error(f"gRPC error sending command: {e}")
            return False, str(e)

    def send_firmware_upgrade(
        self,
        device_id: str,
        firmware_version: str,
        firmware_url: str,
        file_hash: str,
        file_size: int,
        qos: int = 1
    ) -> tuple[bool, str]:
        """
        发送固件升级命令
        返回: (是否成功, 升级ID或错误信息)
        """
        if not self.stub:
            return False, "MQTT Gateway not connected"

        try:
            request = SendFirmwareUpgradeRequest(
                device_id=device_id,
                firmware_version=firmware_version,
                firmware_url=firmware_url,
                file_hash=file_hash,
                file_size=file_size,
                qos=qos
            )
            response = self.stub.SendFirmwareUpgrade(request)
            if response.success:
                return True, response.upgrade_id
            else:
                return False, response.error_message
        except grpc.RpcError as e:
            logger.error(f"gRPC error sending firmware upgrade: {e}")
            return False, str(e)

    def get_connection_status(self) -> dict:
        """获取MQTT连接状态"""
        if not self.stub:
            return {"connected": False, "error": "MQTT Gateway not connected"}

        try:
            request = GetConnectionStatusRequest()
            response = self.stub.GetConnectionStatus(request)
            return {
                "connected": response.connected,
                "broker_address": response.broker_address,
                "client_id": response.client_id,
                "connected_since": response.connected_since,
                "messages_published": response.messages_published,
                "messages_received": response.messages_received
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting connection status: {e}")
            return {"connected": False, "error": str(e)}

    def get_device_online_status(self, device_ids: list[str]) -> dict:
        """获取设备在线状态"""
        if not self.stub:
            return {}

        try:
            request = GetDeviceOnlineStatusRequest(device_ids=device_ids)
            response = self.stub.GetDeviceOnlineStatus(request)
            result = {}
            for status in response.statuses:
                result[status.device_id] = {
                    "online": status.online,
                    "last_seen": status.last_seen
                }
            return result
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting device status: {e}")
            return {}


# 全局客户端实例
mqtt_grpc_client = MqttGrpcClient()
