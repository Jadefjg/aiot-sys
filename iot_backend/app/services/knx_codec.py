"""KNXnet/IP：Tunneling 连接 + 组地址读写"""
import struct
from typing import Any, Dict, List, Tuple


def parse_group_address(text: str) -> int:
    parts = [int(p) for p in str(text or "1/1/1").split("/")]
    if len(parts) == 3:
        return ((parts[0] & 0x1F) << 11) | ((parts[1] & 0x07) << 8) | (parts[2] & 0xFF)
    if len(parts) == 2:
        return ((parts[0] & 0x1F) << 11) | (parts[1] & 0x7FF)
    return int(text)


def _frame(service: int, body: bytes) -> bytes:
    return bytes([0x06, 0x10]) + struct.pack(">HH", service, 6 + len(body)) + body


def encode_search_request(port: int = 3671) -> bytes:
    hpai = bytes([0x08, 0x01, 0x00, 0x00, 0x00, 0x00]) + struct.pack(">H", port)
    return _frame(0x0201, hpai)


def encode_connect_request(port: int = 3671) -> bytes:
    hpai = bytes([0x08, 0x01, 0x00, 0x00, 0x00, 0x00]) + struct.pack(">H", port)
    cri = bytes([0x04, 0x04, 0x02, 0x00])
    return _frame(0x0205, hpai + hpai + cri)


def parse_connect_response(buf: bytes) -> int:
    if len(buf) < 8 or buf[2:4] != b"\x02\x06":
        return 0
    return buf[6]


def encode_tunnel_write(channel: int, seq: int, ga: str, value: Any, bit: bool = True) -> bytes:
    addr = parse_group_address(ga)
    if bit:
        apci_data = 0x80 | (1 if value else 0)
        cemi = bytes([0x11, 0x00, 0xBC, 0xE0, 0x00, 0x00, (addr >> 8) & 0xFF, addr & 0xFF, 0x01, apci_data])
    else:
        raw = int(float(value)) & 0xFF
        cemi = bytes([0x11, 0x00, 0xBC, 0xE0, 0x00, 0x00, (addr >> 8) & 0xFF, addr & 0xFF, 0x02, 0x00, 0x80, raw])
    header = bytes([0x04, channel & 0xFF, seq & 0xFF, 0x00]) + cemi
    return _frame(0x0420, header)


def encode_tunnel_read(channel: int, seq: int, ga: str) -> bytes:
    addr = parse_group_address(ga)
    cemi = bytes([0x11, 0x00, 0xBC, 0xE0, 0x00, 0x00, (addr >> 8) & 0xFF, addr & 0xFF, 0x01, 0x00])
    header = bytes([0x04, channel & 0xFF, seq & 0xFF, 0x00]) + cemi
    return _frame(0x0420, header)


def parse_cemi_value(buf: bytes) -> Tuple[int, Any]:
    """返回 (group_address, value)"""
    idx = buf.find(b"\x29")
    if idx < 0:
        idx = buf.find(b"\x11")
    if idx < 0 or idx + 10 > len(buf):
        return 0, None
    ga = (buf[idx + 6] << 8) | buf[idx + 7]
    length = buf[idx + 8]
    if length <= 1:
        return ga, buf[idx + 9] & 0x3F
    if idx + 10 < len(buf):
        return ga, buf[idx + 10]
    return ga, None


def map_points(ga_value: Dict[int, Any], points: List[dict]) -> Dict[str, Any]:
    out = {}
    for point in points:
        ga = parse_group_address(point.get("group_address") or point.get("address") or "")
        if point.get("name") and ga in ga_value:
            out[point["name"]] = ga_value[ga]
    return out
