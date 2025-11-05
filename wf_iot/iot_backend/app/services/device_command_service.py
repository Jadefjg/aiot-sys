"""
设备命令服务
统一处理所有协议的设备命令发送
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.db.session import SessionLocal
from app.crud.device import device_command_crud
from app.schemas.device import DeviceCommandCreate
from .protocol_manager import protocol_manager

logger = logging.getLogger(__name__)


class DeviceCommandService:
    """
    设备命令服务

    负责:
    1. 根据设备使用的协议路由命令
    2. 标准化命令格式
    3. 记录命令历史和状态
    4. 处理命令响应
    """

    def __init__(self):
        """初始化设备命令服务"""
        self.protocol_manager = protocol_manager
        logger.info("DeviceCommandService initialized")

    async def send_command(
        self,
        device_id: int,
        command_type: str,
        command_data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> Optional[int]:
        """
        发送命令到设备

        Args:
            device_id: 设备数据库ID
            command_type: 命令类型 (control, config, upgrade等)
            command_data: 命令数据
            created_by: 创建者用户ID

        Returns:
            Optional[int]: 创建的命令记录ID，失败返回None
        """
        db = SessionLocal()
        try:
            # 获取设备信息
            from app.crud.device import device_crud
            device = device_crud.get(db, device_id)

            if not device:
                logger.error(f"Device not found: {device_id}")
                return None

            # 准备设备元数据
            device_metadata = {
                "device_id": device.device_id,
                "protocol": device.device_metadata.get("protocol") if device.device_metadata else None,
                **device.device_metadata
            }

            # 检查协议
            if not device_metadata.get("protocol"):
                logger.error(f"Device {device.device_id} has no protocol configured")
                return None

            # 准备协议特定的命令
            protocol_command = self._prepare_protocol_command(
                device_metadata["protocol"],
                command_type,
                command_data
            )

            if not protocol_command:
                logger.error(f"Failed to prepare protocol command for {device_metadata['protocol']}")
                return None

            # 发送命令
            success = await self.protocol_manager.send_command(
                device_metadata,
                protocol_command
            )

            # 创建命令记录
            device_command = DeviceCommandCreate(
                device_id=device_id,
                command_type=command_type,
                command_data=protocol_command
            )

            db_command = device_command_crud.create(db, obj_in=device_command)

            # 更新命令状态
            if success:
                device_command_crud.update_status(
                    db,
                    db_command.id,
                    "sent",
                    {"sent_at": datetime.now()}
                )
                logger.info(
                    f"Command sent successfully: {device.device_id} - {command_type}"
                )
            else:
                device_command_crud.update_status(
                    db,
                    db_command.id,
                    "failed",
                    {"error": "Failed to send command via protocol"}
                )
                logger.error(
                    f"Command failed: {device.device_id} - {command_type}"
                )

            return db_command.id if success else None

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None

        finally:
            db.close()

    def _prepare_protocol_command(
        self,
        protocol: str,
        command_type: str,
        command_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        根据协议类型准备命令格式

        Args:
            protocol: 协议名称
            command_type: 命令类型
            command_data: 原始命令数据

        Returns:
            Optional[Dict[str, Any]]: 协议特定的命令格式
        """
        try:
            if protocol == "mqtt":
                return self._prepare_mqtt_command(command_type, command_data)
            elif protocol == "coap":
                return self._prepare_coap_command(command_type, command_data)
            elif protocol == "amqp":
                return self._prepare_amqp_command(command_type, command_data)
            else:
                logger.error(f"Unsupported protocol: {protocol}")
                return None

        except Exception as e:
            logger.error(f"Error preparing {protocol} command: {e}")
            return None

    def _prepare_mqtt_command(
        self,
        command_type: str,
        command_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备MQTT命令格式

        Args:
            command_type: 命令类型
            command_data: 命令数据

        Returns:
            Dict: MQTT命令
        """
        topic = f"device/{command_data.get('device_id', '')}/command"
        payload = {
            "command_id": command_data.get("command_id"),
            "type": command_type,
            "timestamp": datetime.now().isoformat(),
            "data": command_data.get("data", {})
        }

        return {
            "topic": topic,
            "payload": payload,
            "qos": command_data.get("qos", 1)
        }

    def _prepare_coap_command(
        self,
        command_type: str,
        command_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备CoAP命令格式

        Args:
            command_type: 命令类型
            command_data: 命令数据

        Returns:
            Dict: CoAP命令
        """
        # 根据命令类型映射CoAP资源
        resource_map = {
            "control": "/actuator/control",
            "config": "/config",
            "upgrade": "/firmware/upgrade",
            "query": "/sensor/query"
        }

        resource = resource_map.get(command_type, "/command")
        method_map = {
            "control": "POST",
            "config": "PUT",
            "upgrade": "POST",
            "query": "GET"
        }

        method = method_map.get(command_type, "POST")

        return {
            "resource": resource,
            "method": method,
            "payload": command_data.get("data", {}),
            "content_format": "application/json"
        }

    def _prepare_amqp_command(
        self,
        command_type: str,
        command_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备AMQP命令格式

        Args:
            command_type: 命令类型
            command_data: 命令数据

        Returns:
            Dict: AMQP命令
        """
        routing_key = f"device.{command_data.get('device_id', '')}.command.{command_type}"

        payload = {
            "command_id": command_data.get("command_id"),
            "type": command_type,
            "timestamp": datetime.now().isoformat(),
            "data": command_data.get("data", {})
        }

        properties = {
            "message_id": command_data.get("command_id"),
            "correlation_id": command_data.get("correlation_id"),
            "reply_to": "device.response"
        }

        return {
            "routing_key": routing_key,
            "payload": payload,
            "properties": properties
        }

    async def handle_command_response(
        self,
        protocol: str,
        device_id: str,
        response_data: Dict[str, Any]
    ) -> bool:
        """
        处理设备命令响应

        Args:
            protocol: 协议名称
            device_id: 设备ID
            response_data: 响应数据

        Returns:
            bool: 处理是否成功
        """
        try:
            command_id = response_data.get("command_id")
            status = response_data.get("status", "acknowledged")
            result = response_data.get("result")

            if not command_id:
                logger.warning(f"No command_id in response from {device_id}")
                return False

            db = SessionLocal()
            try:
                # 更新命令状态
                device_command_crud.update_status(
                    db,
                    command_id,
                    status,
                    {
                        "response_data": result,
                        "acknowledged_at": datetime.now()
                    }
                )

                logger.info(
                    f"Command response processed: {device_id} - {status}"
                )
                return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error handling command response: {e}")
            return False

    async def batch_send_command(
        self,
        device_ids: list,
        command_type: str,
        command_data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> Dict[str, int]:
        """
        批量发送命令

        Args:
            device_ids: 设备ID列表
            command_type: 命令类型
            command_data: 命令数据
            created_by: 创建者用户ID

        Returns:
            Dict[str, int]: 设备ID到命令记录的映射
        """
        results = {}

        for device_id in device_ids:
            try:
                command_id = await self.send_command(
                    device_id,
                    command_type,
                    command_data,
                    created_by
                )
                results[str(device_id)] = command_id if command_id else -1

            except Exception as e:
                logger.error(f"Batch command error for device {device_id}: {e}")
                results[str(device_id)] = -1

        return results


# 创建全局设备命令服务实例
device_command_service = DeviceCommandService()
