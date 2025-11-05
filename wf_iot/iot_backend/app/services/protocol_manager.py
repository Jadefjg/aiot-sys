"""
协议管理器
统一管理所有IoT协议服务的生命周期
"""

import logging
from typing import Dict, Any, Optional, List
from .protocol_registry import protocol_registry
from .mqtt_service import mqtt_service
from .coap_service import coap_service
from .amqp_service import amqp_service

logger = logging.getLogger(__name__)


class ProtocolManager:
    """
    协议管理器
    负责初始化、启动、停止所有协议服务
    """

    def __init__(self):
        """初始化协议管理器"""
        self._initialized = False
        logger.info("ProtocolManager initialized")

    def initialize(self):
        """
        初始化所有协议服务

        必须在应用启动时调用
        """
        if self._initialized:
            logger.warning("ProtocolManager already initialized")
            return

        try:
            # 注册所有协议服务
            self._register_services()

            self._initialized = True
            logger.info("ProtocolManager initialized successfully")

        except Exception as e:
            logger.error(f"ProtocolManager initialization failed: {e}")
            raise

    def _register_services(self):
        """注册所有可用的协议服务"""
        logger.info("Registering protocol services...")

        # 注册MQTT服务
        protocol_registry.register("mqtt", mqtt_service)
        logger.info("Registered MQTT service")

        # 条件注册CoAP服务
        try:
            from .coap_service import COAP_AVAILABLE
            if COAP_AVAILABLE:
                protocol_registry.register("coap", coap_service)
                logger.info("Registered CoAP service")
            else:
                logger.warning("CoAP not available (aiocoap not installed)")
        except ImportError:
            logger.warning("CoAP service not available")

        # 条件注册AMQP服务
        try:
            from .amqp_service import AMQP_AVAILABLE
            if AMQP_AVAILABLE:
                protocol_registry.register("amqp", amqp_service)
                logger.info("Registered AMQP service")
            else:
                logger.warning("AMQP not available (pika not installed)")
        except ImportError:
            logger.warning("AMQP service not available")

    async def start_all(self) -> Dict[str, bool]:
        """
        启动所有协议服务

        Returns:
            Dict[str, bool]: 每个协议的启动结果
        """
        logger.info("Starting all protocol services...")
        results = await protocol_registry.start_all()

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        logger.info(f"Protocol services startup: {success_count}/{total_count} successful")

        return results

    async def stop_all(self) -> Dict[str, bool]:
        """
        停止所有协议服务

        Returns:
            Dict[str, bool]: 每个协议的停止结果
        """
        logger.info("Stopping all protocol services...")
        results = await protocol_registry.stop_all()

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        logger.info(f"Protocol services shutdown: {success_count}/{total_count} successful")

        return results

    def get_service_status(self) -> List[Dict[str, Any]]:
        """
        获取所有协议服务状态

        Returns:
            List[Dict]: 协议服务状态列表
        """
        return protocol_registry.get_all_status()

    def is_protocol_supported(self, protocol_name: str) -> bool:
        """
        检查协议是否受支持

        Args:
            protocol_name: 协议名称

        Returns:
            bool: 是否受支持
        """
        return protocol_registry.is_protocol_supported(protocol_name)

    def get_supported_protocols(self) -> List[str]:
        """
        获取所有支持的协议列表

        Returns:
            List[str]: 协议名称列表
        """
        return protocol_registry.list_protocols()

    async def restart_protocol(self, protocol_name: str) -> bool:
        """
        重启指定的协议服务

        Args:
            protocol_name: 协议名称

        Returns:
            bool: 重启是否成功
        """
        service = protocol_registry.get_service(protocol_name)
        if not service:
            logger.error(f"Protocol not found: {protocol_name}")
            return False

        try:
            logger.info(f"Restarting protocol service: {protocol_name}")
            await service.stop()
            success = await service.start()

            if success:
                logger.info(f"Successfully restarted protocol: {protocol_name}")
            else:
                logger.error(f"Failed to restart protocol: {protocol_name}")

            return success

        except Exception as e:
            logger.error(f"Error restarting {protocol_name}: {e}")
            return False

    async def connect_device(
        self,
        device_id: str,
        device_metadata: Dict[str, Any]
    ) -> bool:
        """
        根据设备元数据连接设备

        Args:
            device_id: 设备ID
            device_metadata: 设备元数据 (包含protocol字段)

        Returns:
            bool: 连接是否成功
        """
        protocol = device_metadata.get("protocol")
        if not protocol:
            logger.error(f"Device metadata missing protocol: {device_id}")
            return False

        service = protocol_registry.get_service(protocol)
        if not service:
            logger.error(f"Protocol service not found: {protocol}")
            return False

        try:
            logger.info(f"Connecting device via {protocol}: {device_id}")
            return await service.connect_device(device_id, device_metadata)

        except Exception as e:
            logger.error(f"Device connection error ({protocol}): {e}")
            return False

    async def disconnect_device(self, device_id: str, protocol: str) -> bool:
        """
        断开设备连接

        Args:
            device_id: 设备ID
            protocol: 协议名称

        Returns:
            bool: 断开是否成功
        """
        service = protocol_registry.get_service(protocol)
        if not service:
            return False

        try:
            logger.info(f"Disconnecting device via {protocol}: {device_id}")
            return await service.disconnect_device(device_id)

        except Exception as e:
            logger.error(f"Device disconnection error ({protocol}): {e}")
            return False

    async def send_command(
        self,
        device_metadata: Dict[str, Any],
        command: Dict[str, Any]
    ) -> bool:
        """
        向设备发送命令

        Args:
            device_metadata: 设备元数据
            command: 命令数据

        Returns:
            bool: 发送是否成功
        """
        try:
            return await protocol_registry.send_command_to_device(
                device_metadata,
                command
            )
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return False


# 创建全局协议管理器实例
protocol_manager = ProtocolManager()
