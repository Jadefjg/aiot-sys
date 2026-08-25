"""OPC UA 客户端：优先 asyncua；否则发送 Hello 并按 NodeId 列表读（None 安全策略）"""
import logging
import socket
import struct
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def parse_endpoint(url: str, default_port: int = 4840) -> Tuple[str, int, str]:
    text = url or ""
    if "://" not in text:
        text = "opc.tcp://" + text
    parsed = urlparse(text)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or default_port
    return host, port, text


def encode_string(value: str) -> bytes:
    data = (value or "").encode("utf-8")
    return struct.pack("<i", len(data)) + data


def encode_node_id(node: str) -> bytes:
    text = str(node or "")
    if text.startswith("i="):
        ident = int(text[2:])
        if ident <= 255:
            return bytes([0x00, ident])
        return bytes([0x02, 0x00, 0x00]) + struct.pack("<H", 0)[0:0] + struct.pack("<H", 0) + struct.pack("<I", ident)
    ns, ident = 0, text
    if text.startswith("ns="):
        left, right = text.split(";", 1)
        ns = int(left[3:] or 0)
        ident = right
    if ident.startswith("i="):
        return bytes([0x02]) + struct.pack("<H", ns) + struct.pack("<I", int(ident[2:]))
    if ident.startswith("s="):
        ident = ident[2:]
    return bytes([0x03]) + struct.pack("<H", ns) + encode_string(ident)


def hello_message(endpoint: str) -> bytes:
    body = struct.pack("<IIIII", 0, 65535, 65535, 0, 0) + encode_string(endpoint)
    return b"HEL" + b"F" + struct.pack("<I", 8 + len(body)) + body


def try_hello(host: str, port: int, endpoint: str, timeout: float = 3.0) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        sock.sendall(hello_message(endpoint))
        ack = sock.recv(1024)
        return len(ack) >= 8 and ack[:3] == b"ACK"
    except Exception as exc:
        logger.debug("OPC UA hello %s:%s: %s", host, port, exc)
        return False
    finally:
        sock.close()


def read_nodes(endpoint: str, node_ids: List[str], timeout: float = 5.0) -> Dict[str, Any]:
    """读取 NodeId 列表；asyncua 可用时走完整栈"""
    host, port, url = parse_endpoint(endpoint)
    try:
        return _read_asyncua(url, node_ids, timeout)
    except ImportError:
        logger.info("asyncua 未安装，仅探测 OPC UA Hello")
        try_hello(host, port, url, timeout)
        return {}
    except Exception as exc:
        logger.warning("OPC UA read: %s", exc)
        return {}


def write_nodes(endpoint: str, values: Dict[str, Any], timeout: float = 5.0) -> bool:
    try:
        return _write_asyncua(endpoint, values, timeout)
    except ImportError:
        return False
    except Exception as exc:
        logger.warning("OPC UA write: %s", exc)
        return False


def _read_asyncua(url: str, node_ids: List[str], timeout: float) -> Dict[str, Any]:
    import asyncio
    from asyncua import Client

    async def _run():
        client = Client(url=url, timeout=timeout)
        async with client:
            out = {}
            for node_id in node_ids:
                node = client.get_node(node_id)
                out[node_id] = await node.read_value()
            return out

    return asyncio.run(_run())


def _write_asyncua(url: str, values: Dict[str, Any], timeout: float) -> bool:
    import asyncio
    from asyncua import Client

    async def _run():
        client = Client(url=url, timeout=timeout)
        async with client:
            for node_id, value in values.items():
                await client.get_node(node_id).write_value(value)
            return True

    return bool(asyncio.run(_run()))
