"""西门子 S7：ISO-on-TCP / COTP / S7comm 读写真值"""
import struct
from typing import Any, List, Tuple


def _tpkt(payload: bytes) -> bytes:
    return b"\x03\x00" + struct.pack(">H", 4 + len(payload)) + payload


def cotp_connect(rack: int = 0, slot: int = 1) -> bytes:
    dst = 0x0100 | ((rack & 0x0F) << 4) | (slot & 0x0F)
    cotp = bytes([
        0x11, 0xE0, 0x00, 0x00, 0x00, 0x01, 0x00,
        0xC1, 0x02, 0x01, 0x00,
        0xC2, 0x02, (dst >> 8) & 0xFF, dst & 0xFF,
        0xC0, 0x01, 0x0A,
    ])
    return _tpkt(cotp)


def s7_setup() -> bytes:
    s7 = bytes([
        0x32, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00,
        0xF0, 0x00, 0x00, 0x01, 0x00, 0x01, 0x03, 0xC0,
    ])
    return _tpkt(bytes([0x02, 0xF0, 0x80]) + s7)


def encode_read(db: int, offset: int, size: int, area: int = 0x84) -> bytes:
    """area: 0x81 I / 0x82 Q / 0x83 M / 0x84 DB"""
    start = offset * 8
    item = bytes([
        0x12, 0x0A, 0x10, 0x02, size >> 8, size & 0xFF,
        db >> 8, db & 0xFF, area,
        (start >> 16) & 0xFF, (start >> 8) & 0xFF, start & 0xFF,
    ])
    param = bytes([0x04, 0x01]) + item
    s7 = bytes([0x32, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, len(param), 0x00, 0x00]) + param
    return _tpkt(bytes([0x02, 0xF0, 0x80]) + s7)


def encode_write(db: int, offset: int, data: bytes, area: int = 0x84) -> bytes:
    start = offset * 8
    size = len(data)
    item = bytes([
        0x12, 0x0A, 0x10, 0x02, size >> 8, size & 0xFF,
        db >> 8, db & 0xFF, area,
        (start >> 16) & 0xFF, (start >> 8) & 0xFF, start & 0xFF,
    ])
    param = bytes([0x05, 0x01]) + item
    data_part = bytes([0x00, 0x04, 0x00, size * 8]) + data
    s7 = (
        bytes([0x32, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, len(param)])
        + struct.pack(">H", len(data_part))
        + param
        + data_part
    )
    return _tpkt(bytes([0x02, 0xF0, 0x80]) + s7)


def parse_read_payload(buf: bytes) -> bytes:
    """从 S7 读响应取出数据区"""
    idx = buf.find(b"\x32")
    if idx < 0 or idx + 12 >= len(buf):
        return b""
    param_len = struct.unpack(">H", buf[idx + 6:idx + 8])[0]
    data = buf[idx + 10 + param_len:]
    if len(data) < 4:
        return b""
    return data[4:]


def decode_value(raw: bytes, kind: str = "real") -> Any:
    kind = (kind or "real").lower()
    if not raw:
        return None
    if kind in ("real", "float"):
        if len(raw) < 4:
            return None
        return struct.unpack(">f", raw[:4])[0]
    if kind in ("dint", "int32"):
        return struct.unpack(">i", raw[:4])[0] if len(raw) >= 4 else None
    if kind in ("int", "int16"):
        return struct.unpack(">h", raw[:2])[0] if len(raw) >= 2 else None
    if kind in ("word", "uint16"):
        return struct.unpack(">H", raw[:2])[0] if len(raw) >= 2 else None
    if kind in ("bool", "bit"):
        return bool(raw[0] & 1)
    if kind == "byte":
        return raw[0]
    return list(raw)


def encode_value(value: Any, kind: str = "real") -> bytes:
    kind = (kind or "real").lower()
    if kind in ("real", "float"):
        return struct.pack(">f", float(value))
    if kind in ("dint", "int32"):
        return struct.pack(">i", int(value))
    if kind in ("int", "int16"):
        return struct.pack(">h", int(value))
    if kind in ("word", "uint16"):
        return struct.pack(">H", int(value))
    if kind in ("bool", "bit"):
        return bytes([1 if value else 0])
    return bytes([int(value) & 0xFF])


def point_spec(point: dict) -> Tuple[int, int, int, str]:
    db = int(point.get("db") or 1)
    offset = int(point.get("offset") or point.get("address") or 0)
    kind = point.get("type") or "real"
    size = {"real": 4, "float": 4, "dint": 4, "int32": 4, "int": 2, "int16": 2, "word": 2, "uint16": 2}.get(kind, 1)
    size = int(point.get("size") or size)
    return db, offset, size, kind


def pack_points(points: List[dict], values: dict) -> List[Tuple[dict, bytes]]:
    out = []
    for point in points:
        name = point.get("name")
        if name not in values:
            continue
        _db, _off, _size, kind = point_spec(point)
        out.append((point, encode_value(values[name], kind)))
    return out
