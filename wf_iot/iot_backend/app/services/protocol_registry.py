"""
协议注册器
用于管理所有IoT协议服务的注册、发现和路由
"""

import logging
from typing import Optional, Dict, Any, List
from .protocol_base import ProtocolService

logger = logging.getLogger(__name__)


class ProtocolRegistry:
    """
    协议注册器 - 单例模式
    管理所有已注册的协议服务实例
    """

    _instance = None
    _services: Dict[str, ProtocolService] = {}
    _initialized = False

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ProtocolRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化注册器 (只执行一次)"""
        if not self._initialized:
            self._services = {}
            self._initialized = True
            logger.info("ProtocolRegistry initialized")

    @classmethod
    def register(cls, protocol_name: str, service: ProtocolService) -> bool:
        """
        注册协议服务

        Args:
            protocol_name: 协议名称 (如: mqtt, coap, amqp等)
            service: ProtocolService实例

        Returns:
            bool: 注册是否成功
        """
        instance = cls()
        if protocol_name in instance._services:
            logger.warning(f"Protocol {protocol_name} already registered, replacing...")

        instance._services[protocol_name] = service
        logger.info(f"Registered protocol service: {protocol_name}")
        return True

    @classmethod
    def get_service(cls, protocol_name: str) -> Optional[ProtocolService]:
        """
        获取协议服务实例

        Args:
            protocol_name: 协议名称

        Returns:
            Optional[ProtocolService]: 协议服务实例，如果不存在返回None
        """
        instance = cls()
        service = instance._services.get(protocol_name)
        if service:
            logger.debug(f"Retrieved service for protocol: {protocol_name}")
        else:
            logger.warning(f"No service found for protocol: {protocol_name}")
        return service

    @classmethod
    def get_all_services(cls) -> Dict[str, ProtocolService]:
        """
        获取所有已注册的协议服务

        Returns:
            Dict[str, ProtocolService]: 协议名称到服务实例的映射
        """
        instance = cls()
        return instance._services.copy()

    @classmethod
    def list_protocols(cls) -> List[str]:
        """
        获取所有已注册的协议列表

        Returns:
            List[str]: 协议名称列表
        """
        instance = cls()
        return list(instance._services.keys())

    @classmethod
    def unregister(cls, protocol_name: str) -> bool:
        """
        注销协议服务

        Args:
            protocol_name: 协议名称

        Returns:
            bool: 注销是否成功
        """
        instance = cls()
        if protocol_name in instance._services:
            service = instance._services.pop(protocol_name)
            logger.info(f"Unregistered protocol service: {protocol_name}")
            return True
        else:
            logger.warning(f"Protocol {protocol_name} not found for unregistration")
            return False

    @classmethod
    async def send_command_to_device(
        cls,
        device_metadata: Dict[str, Any],
        command: Dict[str, Any]
    ) -> bool:
        """
        根据设备元数据发送命令到设备

        Args:
            device_metadata: 设备元数据 (包含protocol字段)
            command: 命令数据

        Returns:
            bool: 发送是否成功

        Raises:
            ValueError: 如果不支持的协议
        """
        protocol = device_metadata.get("protocol")
        device_id = device_metadata.get("device_id")

        if not protocol:
            logger.error("Device metadata missing 'protocol' field")
            return False

        if not device_id:
            logger.error("Device metadata missing 'device_id' field")
            return False

        service = cls.get_service(protocol)
        if not service:
            logger.error(f"Unsupported protocol: {protocol}")
            raise ValueError(f"Unsupported protocol: {protocol}")

        logger.info(f"Sending command to {protocol} device: {device_id}")
        return await service.send_command(device_id, command)

    @classmethod
    async def handle_device_message(
        cls,
        protocol: str,
        device_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        处理来自设备的消息

        Args:
            protocol: 协议名称
            device_id: 设备ID
            data: 消息数据

        Returns:
            Optional[Dict]: 标准化后的数据
        """
        service = cls.get_service(protocol)
        if not service:
            logger.error(f"No service available for protocol: {protocol}")
            return None

        logger.debug(f"Handling {protocol} message from device: {device_id}")
        return await service.handle_message(device_id, data)

    @classmethod
    def is_protocol_supported(cls, protocol_name: str) -> bool:
        """
        检查协议是否已注册并可用

        Args:
            protocol_name: 协议名称

        Returns:
            bool: 协议是否可用
        """
        return protocol_name in cls._services

    @classmethod
    def get_service_status(cls, protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        获取协议服务状态

        Args:
            protocol_name: 协议名称

        Returns:
            Optional[Dict]: 服务状态信息
        """
        service = cls.get_service(protocol_name)
        if service:
            return {
                "protocol": protocol_name,
                "connected": service.connected,
                "device_count": len(service.devices),
                "devices": service.list_devices()
            }
        return None

    @classmethod
    def get_all_status(cls) -> List[Dict[str, Any]]:
        """
        获取所有协议服务状态

        Returns:
            List[Dict]: 所有服务状态列表
        """
        return [
            cls.get_service_status(protocol)
            for protocol in cls.list_protocols()
        ]

    @classmethod
    async def start_all(cls) -> Dict[str, bool]:
        """
        启动所有已注册的协议服务

        Returns:
            Dict[str, bool]: 每个协议的启动结果
        """
        results = {}
        logger.info("Starting all protocol services...")

        for protocol_name, service in cls.get_all_services().items():
            try:
                success = await service.start()
                results[protocol_name] = success
                if success:
                    logger.info(f"Started protocol service: {protocol_name}")
                else:
                    logger.error(f"Failed to start protocol service: {protocol_name}")
            except Exception as e:
                logger.error(f"Exception starting {protocol_name}: {e}")
                results[protocol_name] = False

        return results

    @classmethod
    async def stop_all(cls) -> Dict[str, bool]:
        """
        停止所有已注册的协议服务

        Returns:
            Dict[str, bool]: 每个协议的停止结果
        """
        results = {}
        logger.info("Stopping all protocol services...")

        for protocol_name, service in cls.get_all_services().items():
            try:
                success = await service.stop()
                results[protocol_name] = success
                if success:
                    logger.info(f"Stopped protocol service: {protocol_name}")
                else:
                    logger.error(f"Failed to stop protocol service: {protocol_name}")
            except Exception as e:
                logger.error(f"Exception stopping {protocol_name}: {e}")
                results[protocol_name] = False

        return results


# 创建全局实例
protocol_registry = ProtocolRegistry()
