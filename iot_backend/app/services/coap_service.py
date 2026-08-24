"""
CoAP协议服务实现
用于轻量级受限设备的通信
"""

import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime

from .protocol_base import ProtocolService

try:
    import aiocoap
    import aiocoap.resource as resource
    from aiocoap import Message, Context
    COAP_AVAILABLE = True
except ImportError:
    COAP_AVAILABLE = False
    print("Warning: aiocoap not installed. CoAP service will not function.")
    print("Install with: pip install aiocoap")


class CoAPDevice:
    """CoAP设备连接管理"""

    def __init__(self, device_id: str, endpoint: str, resources: Dict[str, str]):
        self.device_id = device_id
        self.endpoint = endpoint
        self.resources = resources
        self.last_seen = datetime.now()
        self.status = "online"


class CoAPService(ProtocolService):
    """
    CoAP协议服务

    特性:
    - 基于UDP的轻量级协议
    - 适合受限设备 (constrained devices)
    - 支持GET、POST、PUT、DELETE方法
    - 最小化资源使用
    """

    def __init__(self):
        """初始化CoAP服务"""
        super().__init__("coap")
        self.context: Optional[Context] = None
        self.devices: Dict[str, CoAPDevice] = {}

    async def connect_device(self, device_id: str, device_config: Dict[str, Any]) -> bool:
        """
        与CoAP设备建立连接

        Args:
            device_id: 设备唯一标识符
            device_config: 设备配置 (endpoint, resources等)

        Returns:
            bool: 连接是否成功
        """
        try:
            endpoint = device_config.get("endpoint")
            resources = device_config.get("resources", {})

            if not endpoint:
                self._log_message("ERROR", "Device endpoint not provided", device_id)
                return False

            # 创建设备连接
            device = CoAPDevice(
                device_id=device_id,
                endpoint=endpoint,
                resources=resources
            )

            # 测试连接 (发送GET请求到心跳资源)
            test_resource = resources.get("heartbeat", "/.well-known/core")
            response = await self._send_request(device_id, "GET", test_resource)

            if response:
                self.devices[device_id] = device
                device.last_seen = datetime.now()
                self._log_message("INFO", f"Connected to CoAP device: {endpoint}", device_id)
                return True
            else:
                self._log_message("WARNING", "Device did not respond to test request", device_id)
                return False

        except Exception as e:
            self._log_message("ERROR", f"Connection failed: {e}", device_id)
            return False

    async def disconnect_device(self, device_id: str) -> bool:
        """
        断开CoAP设备连接

        Args:
            device_id: 设备唯一标识符

        Returns:
            bool: 断开是否成功
        """
        if device_id in self.devices:
            device = self.devices.pop(device_id)
            self._log_message("INFO", f"Disconnected from CoAP device: {device.endpoint}", device_id)
            return True
        else:
            self._log_message("WARNING", f"Device not found for disconnection: {device_id}", device_id)
            return False

    async def send_command(self, device_id: str, command: Dict[str, Any]) -> bool:
        """
        向CoAP设备发送命令

        Args:
            device_id: 设备唯一标识符
            command: 命令数据 {
                "resource": str,  # 资源路径
                "method": str,    # HTTP方法 (GET/POST/PUT/DELETE)
                "payload": dict,  # 可选，数据负载
                "content_format": str  # 可选，内容格式 (如: application/json)
            }

        Returns:
            bool: 发送是否成功
        """
        device = self.devices.get(device_id)
        if not device:
            self._log_message("ERROR", f"Device not connected: {device_id}", device_id)
            return False

        try:
            resource_path = command.get("resource")
            method = command.get("method", "GET").upper()
            payload = command.get("payload")
            content_format = command.get("content_format", "application/json")

            if not resource_path:
                self._log_message("ERROR", "Command resource path not specified", device_id)
                return False

            # 构建资源路径
            full_path = f"{device.endpoint}/{resource_path.lstrip('/')}"

            # 发送请求
            response = await self._send_request(
                device_id,
                method,
                full_path,
                payload=payload,
                content_format=content_format
            )

            if response:
                device.last_seen = datetime.now()
                self._log_message("INFO", f"Command sent successfully: {method} {resource_path}", device_id)
                return True
            else:
                self._log_message("ERROR", f"Command failed: {method} {resource_path}", device_id)
                return False

        except Exception as e:
            self._log_message("ERROR", f"Send command exception: {e}", device_id)
            return False

    async def handle_message(self, device_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理来自CoAP设备的消息

        Args:
            device_id: 设备ID
            data: 原始CoAP消息数据

        Returns:
            Optional[Dict]: 标准化后的数据
        """
        try:
            device = self.devices.get(device_id)
            if not device:
                self._log_message("WARNING", f"Unknown device: {device_id}", device_id)
                return None

            # 标准化数据
            normalized = self._normalize_data(
                device_id=device_id,
                protocol=self.protocol_name,
                raw_data=data,
                data_type=data.get("type", "telemetry")
            )

            device.last_seen = datetime.now()
            device.status = "online"

            self._log_message("DEBUG", f"Processed message from CoAP device", device_id)
            return normalized

        except Exception as e:
            self._log_message("ERROR", f"Message handling failed: {e}", device_id)
            return None

    async def _send_request(
        self,
        device_id: str,
        method: str,
        resource_path: str,
        payload: Optional[Dict] = None,
        content_format: str = "application/json"
    ) -> Optional[Dict[str, Any]]:
        """
        发送CoAP请求

        Args:
            device_id: 设备ID
            method: HTTP方法
            resource_path: 资源路径
            payload: 可选的数据负载
            content_format: 内容格式

        Returns:
            Optional[Dict]: 响应数据
        """
        if not COAP_AVAILABLE or not self.context:
            self._log_message("ERROR", "CoAP not available or context not initialized", device_id)
            return None

        try:
            # 构建CoAP消息
            uri = resource_path
            message = Message(code=method, uri=uri)

            # 添加负载
            if payload:
                if content_format == "application/json":
                    message.payload = json.dumps(payload).encode('utf-8')
                else:
                    message.payload = str(payload).encode('utf-8')

                # 设置内容格式选项
                if content_format == "application/json":
                    message.opt.content_format = aiocoap.media_types.codes['application/json']

            # 发送请求
            request = self.context.request(message)
            response = await request.response

            # 解析响应
            if response:
                try:
                    response_data = json.loads(response.payload.decode('utf-8'))
                    return {
                        "status": "success",
                        "code": str(response.code),
                        "payload": response_data,
                        "timestamp": datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    return {
                        "status": "success",
                        "code": str(response.code),
                        "payload": response.payload.decode('utf-8'),
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return None

        except Exception as e:
            self._log_message("ERROR", f"Request failed: {e}", device_id)
            return None

    async def start(self) -> bool:
        """
        启动CoAP服务

        Returns:
            bool: 启动是否成功
        """
        try:
            if not COAP_AVAILABLE:
                self._log_message("ERROR", "aiocoap library not installed")
                return False

            self.context = await Context.create_client_context()
            self.connected = True
            self._log_message("INFO", "CoAP service started successfully")
            return True

        except Exception as e:
            self._log_message("ERROR", f"Failed to start CoAP service: {e}")
            return False

    async def stop(self) -> bool:
        """
        停止CoAP服务

        Returns:
            bool: 停止是否成功
        """
        try:
            # 断开所有设备连接
            for device_id in list(self.devices.keys()):
                await self.disconnect_device(device_id)

            # 关闭上下文
            if self.context:
                self.context = None

            self.connected = False
            self._log_message("INFO", "CoAP service stopped")
            return True

        except Exception as e:
            self._log_message("ERROR", f"Failed to stop CoAP service: {e}")
            return False

    async def discover_resources(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        发现CoAP设备资源

        Args:
            device_id: 设备ID

        Returns:
            Optional[Dict]: 发现的资源列表
        """
        device = self.devices.get(device_id)
        if not device:
            return None

        try:
            # 使用CoAP资源发现
            response = await self._send_request(
                device_id,
                "GET",
                f"{device.endpoint}/.well-known/core"
            )

            if response and response.get("payload"):
                self._log_message("INFO", "Resource discovery successful", device_id)
                return response["payload"]

            return None

        except Exception as e:
            self._log_message("ERROR", f"Resource discovery failed: {e}", device_id)
            return None


# 创建全局CoAP服务实例
coap_service = CoAPService()
