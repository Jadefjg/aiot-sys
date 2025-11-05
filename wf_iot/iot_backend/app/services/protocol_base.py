"""
协议抽象基类
定义所有IoT协议必须实现的通用接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProtocolService(ABC):
    """所有IoT协议的抽象基类"""

    def __init__(self, protocol_name: str):
        """
        初始化协议服务

        Args:
            protocol_name: 协议名称 (如: mqtt, coap, amqp等)
        """
        self.protocol_name = protocol_name
        self.connected = False
        self.devices: Dict[str, Dict[str, Any]] = {}  # 存储已连接的设备

    @abstractmethod
    async def connect_device(self, device_id: str, device_config: Dict[str, Any]) -> bool:
        """
        与设备建立连接

        Args:
            device_id: 设备唯一标识符
            device_config: 设备配置信息 (包含endpoint、credentials等)

        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    async def disconnect_device(self, device_id: str) -> bool:
        """
        断开设备连接

        Args:
            device_id: 设备唯一标识符

        Returns:
            bool: 断开是否成功
        """
        pass

    @abstractmethod
    async def send_command(self, device_id: str, command: Dict[str, Any]) -> bool:
        """
        向设备发送命令

        Args:
            device_id: 设备唯一标识符
            command: 命令数据

        Returns:
            bool: 发送是否成功
        """
        pass

    @abstractmethod
    async def handle_message(self, device_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理来自设备的消息

        Args:
            device_id: 设备唯一标识符
            data: 原始消息数据

        Returns:
            Optional[Dict]: 标准化后的消息数据，如果处理失败返回None
        """
        pass

    @abstractmethod
    async def start(self) -> bool:
        """
        启动协议服务

        Returns:
            bool: 启动是否成功
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        停止协议服务

        Returns:
            bool: 停止是否成功
        """
        pass

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备连接状态

        Args:
            device_id: 设备唯一标识符

        Returns:
            Optional[Dict]: 设备状态信息
        """
        return self.devices.get(device_id)

    def list_devices(self) -> List[str]:
        """
        获取已连接设备列表

        Returns:
            List[str]: 设备ID列表
        """
        return list(self.devices.keys())

    def _normalize_data(
        self,
        device_id: str,
        protocol: str,
        raw_data: Dict[str, Any],
        data_type: str = "telemetry"
    ) -> Dict[str, Any]:
        """
        标准化协议特定数据为通用格式

        Args:
            device_id: 设备ID
            protocol: 协议名称
            raw_data: 原始数据
            data_type: 数据类型 (telemetry, event, alarm等)

        Returns:
            Dict: 标准化后的数据
        """
        return {
            "device_id": device_id,
            "protocol": protocol,
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "data": raw_data.get("payload", raw_data),
            "quality": raw_data.get("quality", "good"),
            "raw_message": raw_data  # 保留原始消息以备调试
        }

    def _log_message(self, level: str, message: str, device_id: Optional[str] = None):
        """
        统一的日志记录方法

        Args:
            level: 日志级别 (INFO, WARNING, ERROR)
            message: 日志消息
            device_id: 可选的设备ID
        """
        import logging

        logger = logging.getLogger(f"{__name__}.{self.protocol_name}")
        device_info = f" [Device: {device_id}]" if device_id else ""
        log_message = f"{self.protocol_name.upper()}{device_info}: {message}"

        if level == "INFO":
            logger.info(log_message)
        elif level == "WARNING":
            logger.warning(log_message)
        elif level == "ERROR":
            logger.error(log_message)
        elif level == "DEBUG":
            logger.debug(log_message)
