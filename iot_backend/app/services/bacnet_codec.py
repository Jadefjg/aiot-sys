"""BACnet/IP：Who-Is / ReadProperty / WriteProperty（Present Value）"""
import struct
from typing import Any, Dict, List, Optional, Tuple

BVLC_UNICAST = 0x0A
OBJECT_AI, OBJECT_AO, OBJECT_AV = 0, 1, 2
OBJECT_BI, OBJECT_BO, OBJECT_BV = 3, 4, 5
PROP_PRESENT_VALUE = 85

OBJECT_TYPES = {
    "analogInput": OBJECT_AI, "ai": OBJECT_AI,
    "analogOutput": OBJECT_AO, "ao": OBJECT_AO,
    "analogValue": OBJECT_AV, "av": OBJECT_AV,
    "binaryInput": OBJECT_BI, "bi": OBJECT_BI,
    "binaryOutput": OBJECT_BO, "bo": OBJECT_BO,
    "binaryValue": OBJECT_BV, "bv": OBJECT_BV,
}


def _bvlc(npdu_apdu: bytes) -> bytes:
    return bytes([0x81, BVLC_UNICAST]) + struct.pack(">H", 4 + len(npdu_apdu)) + npdu_apdu


def _npdu(apdu: bytes, dest: Optional[int] = None) -> bytes:
    if dest is None:
        return bytes([0x01, 0x04]) + apdu
    dnet = b"\x00\x00"
    return bytes([0x01, 0x24]) + dnet + bytes([0x00, 0xFF]) + apdu


def _object_id(obj_type: int, instance: int) -> bytes:
    packed = ((obj_type & 0x3FF) << 22) | (instance & 0x3FFFFF)
    return struct.pack(">I", packed)


def encode_who_is() -> bytes:
    apdu = bytes([0x10, 0x08])
    return _bvlc(_npdu(apdu))


def encode_read_property(invoke_id: int, obj_type: int, instance: int, prop: int = PROP_PRESENT_VALUE) -> bytes:
    apdu = bytes([0x00, 0x02, invoke_id & 0xFF, 0x0C])
    apdu += bytes([0x0C]) + _object_id(obj_type, instance)
    apdu += bytes([0x19, prop & 0xFF])
    return _bvlc(_npdu(apdu))


def encode_write_property(
    invoke_id: int, obj_type: int, instance: int, value: Any, prop: int = PROP_PRESENT_VALUE
) -> bytes:
    apdu = bytes([0x00, 0x04, invoke_id & 0xFF, 0x0F])
    apdu += bytes([0x0C]) + _object_id(obj_type, instance)
    apdu += bytes([0x19, prop & 0xFF])
    if isinstance(value, bool):
        encoded = bytes([0x91, 0x01 if value else 0x00])
    else:
        encoded = bytes([0x44]) + struct.pack(">f", float(value))
    apdu += bytes([0x3E]) + encoded + bytes([0x3F])
    return _bvlc(_npdu(apdu))


def parse_object_id(buf: bytes) -> Tuple[int, int]:
    packed = struct.unpack(">I", buf[:4])[0]
    return (packed >> 22) & 0x3FF, packed & 0x3FFFFF


def parse_present_value(buf: bytes) -> Optional[float]:
    """从复杂 ACK 中取出 Real / Enumerated / Boolean"""
    if b"\x44" in buf:
        i = buf.index(b"\x44")
        if i + 5 <= len(buf):
            return struct.unpack(">f", buf[i + 1:i + 5])[0]
    if b"\x91" in buf:
        i = buf.index(b"\x91")
        if i + 2 <= len(buf):
            return float(buf[i + 1])
    if b"\x21" in buf:
        i = buf.index(b"\x21")
        if i + 2 <= len(buf):
            return float(buf[i + 1])
    return None


def object_from_point(point: dict) -> Tuple[int, int]:
    kind = str(point.get("object_type") or point.get("type") or "analogInput")
    obj_type = OBJECT_TYPES.get(kind, OBJECT_AI)
    if kind.isdigit():
        obj_type = int(kind)
    instance = int(point.get("instance") or point.get("object_instance") or 1)
    return obj_type, instance


def map_reads(points: List[dict], values: List[Optional[float]]) -> Dict[str, Any]:
    out = {}
    for point, value in zip(points, values):
        if point.get("name") and value is not None:
            out[point["name"]] = value
    return out
