"""Modbus TCP 编解码（功能码 03/04/06/16）"""
import struct
from typing import List, Optional, Tuple


def build_read(unit: int, address: int, quantity: int, func: int = 3, tid: int = 1) -> bytes:
    pdu = bytes([func, (address >> 8) & 0xFF, address & 0xFF, (quantity >> 8) & 0xFF, quantity & 0xFF])
    return struct.pack(">HHHB", tid & 0xFFFF, 0, len(pdu) + 1, unit & 0xFF) + pdu


def build_write_single(unit: int, address: int, value: int, tid: int = 1) -> bytes:
    pdu = bytes([6, (address >> 8) & 0xFF, address & 0xFF, (value >> 8) & 0xFF, value & 0xFF])
    return struct.pack(">HHHB", tid & 0xFFFF, 0, len(pdu) + 1, unit & 0xFF) + pdu


def build_write_multi(unit: int, address: int, values: List[int], tid: int = 1) -> bytes:
    qty = len(values)
    payload = b"".join(struct.pack(">H", v & 0xFFFF) for v in values)
    pdu = bytes([16, (address >> 8) & 0xFF, address & 0xFF, (qty >> 8) & 0xFF, qty & 0xFF, qty * 2]) + payload
    return struct.pack(">HHHB", tid & 0xFFFF, 0, len(pdu) + 1, unit & 0xFF) + pdu


def parse_mbap(data: bytes) -> Optional[Tuple[int, int, bytes]]:
    if not data or len(data) < 8:
        return None
    tid, _proto, length, unit = struct.unpack(">HHHB", data[:7])
    pdu = data[7:7 + max(length - 1, 0)]
    return tid, unit, pdu


def parse_read_registers(pdu: bytes) -> List[int]:
    if not pdu or pdu[0] & 0x80:
        return []
    count = pdu[1] if len(pdu) > 1 else 0
    body = pdu[2:2 + count]
    regs = []
    for i in range(0, len(body) - 1, 2):
        regs.append((body[i] << 8) | body[i + 1])
    return regs


def decode_point(regs: List[int], point: dict) -> Optional[float]:
    """按点表把寄存器解码为属性值"""
    if not regs:
        return None
    ptype = (point.get("type") or "uint16").lower()
    raw = regs[0]
    if ptype in ("int16", "sint16") and raw >= 0x8000:
        raw -= 0x10000
    elif ptype in ("uint32", "int32", "float32") and len(regs) >= 2:
        raw = (regs[0] << 16) | regs[1]
        if ptype == "int32" and raw >= 0x80000000:
            raw -= 0x100000000
        if ptype == "float32":
            raw = struct.unpack(">f", struct.pack(">I", raw & 0xFFFFFFFF))[0]
    scale = point.get("scale", 1) or 1
    offset = point.get("offset", 0) or 0
    return raw * scale + offset


def encode_point(value, point: dict) -> List[int]:
    scale = point.get("scale", 1) or 1
    raw = int(round(float(value) / scale))
    ptype = (point.get("type") or "uint16").lower()
    if ptype in ("uint32", "int32", "float32"):
        if ptype == "float32":
            raw = struct.unpack(">I", struct.pack(">f", float(value)))[0]
        return [(raw >> 16) & 0xFFFF, raw & 0xFFFF]
    return [raw & 0xFFFF]
