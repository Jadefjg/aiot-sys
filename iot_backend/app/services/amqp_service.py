"""
AMQP协议服务实现
用于企业级IoT消息传递
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

from .protocol_base import ProtocolService

try:
    import pika
    from pika import channel, connection
    AMQP_AVAILABLE = True
except ImportError:
    AMQP_AVAILABLE = False
    print("Warning: pika not installed. AMQP service will not function.")
    print("Install with: pip install pika")


class AMQPConnection:
    """AMQP连接管理"""

    def __init__(
        self,
        device_id: str,
        connection: connection.Connection,
        channel: channel.Channel,
        exchange: str,
        routing_key: str
    ):
        self.device_id = device_id
        self.connection = connection
        self.channel = channel
        self.exchange = exchange
        self.routing_key = routing_key
        self.last_seen = datetime.now()
        self.status = "online"


class AMQPService(ProtocolService):
    """
    AMQP协议服务

    特性:
    - 可靠的消息传递
    - 支持事务和确认
    - 企业级可扩展性
    - 适合高吞吐量场景
    - 支持路由和交换机
    """

    def __init__(self):
        """初始化AMQP服务"""
        super().__init__("amqp")
        self.connections: Dict[str, AMQPConnection] = {}
        self.connection_params: Optional[pika.ConnectionParameters] = None
        self.default_exchange = "iot_devices"

    async def connect_device(self, device_id: str, device_config: Dict[str, Any]) -> bool:
        """
        与AMQP设备建立连接

        Args:
            device_id: 设备唯一标识符
            device_config: 设备配置 (host, port, exchange, routing_key等)

        Returns:
            bool: 连接是否成功
        """
        if not AMQP_AVAILABLE:
            self._log_message("ERROR", "pika library not installed")
            return False

        try:
            # 读取配置
            host = device_config.get("host", "localhost")
            port = device_config.get("port", 5672)
            exchange = device_config.get("exchange", self.default_exchange)
            routing_key = device_config.get("routing_key", f"device.{device_id}")
            username = device_config.get("username")
            password = device_config.get("password")

            # 建立连接
            credentials = None
            if username and password:
                credentials = pika.PlainCredentials(username, password)

            self.connection_params = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            # 创建连接和通道
            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()

            # 声明交换机
            channel.exchange_declare(
                exchange=exchange,
                exchange_type='topic',
                durable=True
            )

            # 创建队列用于接收消息
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            # 绑定队列
            channel.queue_bind(
                exchange=exchange,
                queue=queue_name,
                routing_key=f"{routing_key}.*"
            )

            # 启动消费
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=lambda ch, method, props, body: self._on_message(
                    device_id, ch, method, props, body
                ),
                auto_ack=False
            )

            # 存储连接
            amqp_conn = AMQPConnection(
                device_id=device_id,
                connection=connection,
                channel=channel,
                exchange=exchange,
                routing_key=routing_key
            )

            self.connections[device_id] = amqp_conn
            self.devices[device_id] = {
                "status": "online",
                "last_seen": datetime.now(),
                "exchange": exchange,
                "routing_key": routing_key
            }

            # 在单独的线程中启动事件循环
            channel.start_consuming()
            self._log_message("INFO", f"Connected to AMQP device via exchange: {exchange}", device_id)
            return True

        except Exception as e:
            self._log_message("ERROR", f"Connection failed: {e}", device_id)
            return False

    def _on_message(
        self,
        device_id: str,
        channel,
        method,
        properties,
        body: bytes
    ):
        """
        AMQP消息回调

        Args:
            device_id: 设备ID
            channel: AMQP通道
            method: 投递方法
            properties: 消息属性
            body: 消息体
        """
        try:
            # 解析消息
            data_str = body.decode('utf-8')
            data = json.loads(data_str)

            # 更新设备状态
            if device_id in self.devices:
                self.devices[device_id]["last_seen"] = datetime.now()

            # 发送确认
            channel.basic_ack(delivery_tag=method.delivery_tag)

            self._log_message(
                "DEBUG",
                f"Received AMQP message: {data_str[:100]}",
                device_id
            )

        except Exception as e:
            self._log_message("ERROR", f"Message handling failed: {e}", device_id)
            # 拒绝消息
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def disconnect_device(self, device_id: str) -> bool:
        """
        断开AMQP设备连接

        Args:
            device_id: 设备唯一标识符

        Returns:
            bool: 断开是否成功
        """
        if device_id in self.connections:
            amqp_conn = self.connections.pop(device_id)

            try:
                amqp_conn.channel.stop_consuming()
                amqp_conn.channel.close()
                amqp_conn.connection.close()

                self._log_message(
                    "INFO",
                    f"Disconnected from AMQP device: {amqp_conn.exchange}",
                    device_id
                )
                return True

            except Exception as e:
                self._log_message(
                    "ERROR",
                    f"Disconnect error: {e}",
                    device_id
                )
                return False
        else:
            self._log_message(
                "WARNING",
                f"Device not found for disconnection: {device_id}",
                device_id
            )
            return False

    async def send_command(self, device_id: str, command: Dict[str, Any]) -> bool:
        """
        向AMQP设备发送命令

        Args:
            device_id: 设备唯一标识符
            command: 命令数据 {
                "routing_key": str,  # 可选，默认使用设备的routing_key
                "payload": dict,     # 消息负载
                "properties": dict   # 可选，消息属性
            }

        Returns:
            bool: 发送是否成功
        """
        amqp_conn = self.connections.get(device_id)
        if not amqp_conn:
            self._log_message("ERROR", f"Device not connected: {device_id}", device_id)
            return False

        try:
            # 获取命令参数
            routing_key = command.get("routing_key", amqp_conn.routing_key)
            payload = command.get("payload", {})
            properties = command.get("properties", {})

            # 序列化负载
            body = json.dumps(payload).encode('utf-8')

            # 设置消息属性
            msg_properties = pika.BasicProperties(
                delivery_mode=2,  # 持久化
                message_id=properties.get("message_id"),
                correlation_id=properties.get("correlation_id"),
                reply_to=properties.get("reply_to"),
                timestamp=int(datetime.now().timestamp())
            )

            # 发布消息
            amqp_conn.channel.basic_publish(
                exchange=amqp_conn.exchange,
                routing_key=routing_key,
                body=body,
                properties=msg_properties
            )

            # 更新设备状态
            amqp_conn.last_seen = datetime.now()

            self._log_message(
                "INFO",
                f"Command sent successfully via routing_key: {routing_key}",
                device_id
            )
            return True

        except Exception as e:
            self._log_message("ERROR", f"Send command failed: {e}", device_id)
            return False

    async def handle_message(self, device_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理来自AMQP设备的消息

        Args:
            device_id: 设备ID
            data: 原始AMQP消息数据

        Returns:
            Optional[Dict]: 标准化后的数据
        """
        try:
            # 更新设备状态
            if device_id in self.devices:
                self.devices[device_id]["last_seen"] = datetime.now()

            # 标准化数据
            normalized = self._normalize_data(
                device_id=device_id,
                protocol=self.protocol_name,
                raw_data=data,
                data_type=data.get("type", "telemetry")
            )

            # 添加AMQP特有信息
            normalized["amqp"] = {
                "exchange": data.get("exchange"),
                "routing_key": data.get("routing_key"),
                "delivery_tag": data.get("delivery_tag")
            }

            self._log_message("DEBUG", "Processed AMQP message", device_id)
            return normalized

        except Exception as e:
            self._log_message("ERROR", f"Message handling failed: {e}", device_id)
            return None

    async def start(self) -> bool:
        """
        启动AMQP服务

        Returns:
            bool: 启动是否成功
        """
        try:
            if not AMQP_AVAILABLE:
                self._log_message("ERROR", "pika library not installed")
                return False

            self.connected = True
            self._log_message("INFO", "AMQP service started")
            return True

        except Exception as e:
            self._log_message("ERROR", f"Failed to start AMQP service: {e}")
            return False

    async def stop(self) -> bool:
        """
        停止AMQP服务

        Returns:
            bool: 停止是否成功
        """
        try:
            # 断开所有设备连接
            for device_id in list(self.connections.keys()):
                await self.disconnect_device(device_id)

            self.connected = False
            self._log_message("INFO", "AMQP service stopped")
            return True

        except Exception as e:
            self._log_message("ERROR", f"Failed to stop AMQP service: {e}")
            return False

    async def create_queue(self, device_id: str, queue_name: str, durable: bool = True) -> bool:
        """
        为设备创建专用队列

        Args:
            device_id: 设备ID
            queue_name: 队列名称
            durable: 是否持久化

        Returns:
            bool: 创建是否成功
        """
        amqp_conn = self.connections.get(device_id)
        if not amqp_conn:
            return False

        try:
            amqp_conn.channel.queue_declare(
                queue=queue_name,
                durable=durable
            )
            self._log_message("INFO", f"Created queue: {queue_name}", device_id)
            return True

        except Exception as e:
            self._log_message("ERROR", f"Queue creation failed: {e}", device_id)
            return False


# 创建全局AMQP服务实例
amqp_service = AMQPService()
