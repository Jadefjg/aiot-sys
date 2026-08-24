# MQTT Gateway gRPC服务端实现

import grpc
import json
import uuid
from concurrent import futures
import sys
import os

# 添加proto生成代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../proto/generated'))

from mqtt_gateway_pb2 import (
    PublishResponse, BatchPublishResponse, SubscribeResponse, UnsubscribeResponse,
    SendCommandResponse, SendUpgradeResponse, ConnectionStatusResponse,
    DeviceOnlineStatusResponse, DeviceOnlineStatus
)
import mqtt_gateway_pb2_grpc

from app.mqtt.client import mqtt_client
from app.core.config import settings


class MqttGatewayServicer(mqtt_gateway_pb2_grpc.MqttGatewayServiceServicer):
    """MQTT Gateway gRPC服务实现"""

    def PublishMessage(self, request, context):
        """发布消息到MQTT主题"""
        topic = request.topic
        payload = request.payload.decode('utf-8') if isinstance(request.payload, bytes) else str(request.payload)
        qos = request.qos
        retain = request.retain

        success, message_id = mqtt_client.publish(topic, payload, qos, retain)

        return PublishResponse(
            success=success,
            message_id=message_id if success else "",
            error_message="" if success else message_id
        )

    def BatchPublishMessage(self, request, context):
        """批量发布消息"""
        published_count = 0
        failed_count = 0
        failed_topics = []

        for msg in request.messages:
            topic = msg.topic
            payload = msg.payload.decode('utf-8') if isinstance(msg.payload, bytes) else str(msg.payload)
            qos = msg.qos
            retain = msg.retain

            success, _ = mqtt_client.publish(topic, payload, qos, retain)
            if success:
                published_count += 1
            else:
                failed_count += 1
                failed_topics.append(topic)

        return BatchPublishResponse(
            success=failed_count == 0,
            published_count=published_count,
            failed_count=failed_count,
            failed_topics=failed_topics,
            error_message="" if failed_count == 0 else f"{failed_count} messages failed to publish"
        )

    def SubscribeTopic(self, request, context):
        """订阅主题"""
        topic = request.topic
        qos = request.qos

        success, error_msg = mqtt_client.subscribe(topic, qos)

        return SubscribeResponse(
            success=success,
            error_message=error_msg
        )

    def UnsubscribeTopic(self, request, context):
        """取消订阅"""
        topic = request.topic

        success, error_msg = mqtt_client.unsubscribe(topic)

        return UnsubscribeResponse(
            success=success,
            error_message=error_msg
        )

    def SendDeviceCommand(self, request, context):
        """发送设备命令"""
        device_id = request.device_id
        command_type = request.command_type
        command_data = dict(request.command_data.fields) if request.command_data else {}
        timeout_seconds = request.timeout_seconds
        qos = request.qos if request.qos else 1

        # 构建命令主题和消息
        topic = f"device/{device_id}/command"
        command_id = str(uuid.uuid4())

        payload = json.dumps({
            "command_id": command_id,
            "command_type": command_type,
            "data": command_data,
            "timeout": timeout_seconds
        }, ensure_ascii=False)

        success, error_msg = mqtt_client.publish(topic, payload, qos)

        return SendCommandResponse(
            success=success,
            command_id=command_id if success else "",
            error_message="" if success else error_msg
        )

    def SendFirmwareUpgrade(self, request, context):
        """发送固件升级命令"""
        device_id = request.device_id
        firmware_version = request.firmware_version
        firmware_url = request.firmware_url
        file_hash = request.file_hash
        file_size = request.file_size
        qos = request.qos if request.qos else 1

        # 构建固件升级主题和消息
        topic = f"device/{device_id}/firmware/upgrade"
        upgrade_id = str(uuid.uuid4())

        payload = json.dumps({
            "upgrade_id": upgrade_id,
            "version": firmware_version,
            "url": firmware_url,
            "hash": file_hash,
            "size": file_size
        }, ensure_ascii=False)

        success, error_msg = mqtt_client.publish(topic, payload, qos)

        return SendUpgradeResponse(
            success=success,
            upgrade_id=upgrade_id if success else "",
            error_message="" if success else error_msg
        )

    def GetConnectionStatus(self, request, context):
        """获取MQTT连接状态"""
        connected_since = 0
        if mqtt_client.connected_since:
            connected_since = int(mqtt_client.connected_since.timestamp())

        return ConnectionStatusResponse(
            connected=mqtt_client.connected,
            broker_address=f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
            client_id=settings.MQTT_CLIENT_ID,
            connected_since=connected_since,
            messages_published=mqtt_client.messages_published,
            messages_received=mqtt_client.messages_received,
            error_message=""
        )

    def GetDeviceOnlineStatus(self, request, context):
        """获取设备在线状态"""
        device_ids = list(request.device_ids)
        statuses = mqtt_client.get_device_online_status(device_ids)

        status_list = []
        for device_id, status_info in statuses.items():
            status_list.append(DeviceOnlineStatus(
                device_id=device_id,
                online=status_info.get("online", False),
                last_seen=status_info.get("last_seen", "") or ""
            ))

        return DeviceOnlineStatusResponse(
            success=True,
            statuses=status_list,
            error_message=""
        )


def serve_grpc():
    """启动gRPC服务"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mqtt_gateway_pb2_grpc.add_MqttGatewayServiceServicer_to_server(MqttGatewayServicer(), server)
    server.add_insecure_port(f'[::]:{settings.GRPC_PORT}')
    server.start()
    print(f"MQTT Gateway gRPC服务启动在端口 {settings.GRPC_PORT}")
    return server
