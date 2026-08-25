"""IEC 60870-5-104：APCI + ASDU 总召唤 / 遥测解析 / 遥控"""
import struct
from typing import Any, Dict, List, Tuple


STARTDT_ACT = bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00])
STARTDT_CON = bytes([0x68, 0x04, 0x0B, 0x00, 0x00, 0x00])
STOPDT_ACT = bytes([0x68, 0x04, 0x13, 0x00, 0x00, 0x00])
TESTFR_ACT = bytes([0x68, 0x04, 0x43, 0x00, 0x00, 0x00])

TYPE_SP = 1
TYPE_ME_NB = 11
TYPE_ME_NC = 13
TYPE_IC = 100
TYPE_SC = 45
TYPE_SE_NC = 50


def _apci_i(ssn: int, rsn: int, asdu: bytes) -> bytes:
    length = 4 + len(asdu)
    ctrl = struct.pack("<HH", (ssn << 1) & 0xFFFE, (rsn << 1) & 0xFFFE)
    return bytes([0x68, length]) + ctrl + asdu


def _ioa(addr: int) -> bytes:
    return bytes([addr & 0xFF, (addr >> 8) & 0xFF, (addr >> 16) & 0xFF])


def general_interrogation(ca: int = 1, ssn: int = 0, rsn: int = 0) -> bytes:
    asdu = bytes([TYPE_IC, 1, 6, 0]) + struct.pack("<H", ca) + _ioa(0) + bytes([20])
    return _apci_i(ssn, rsn, asdu)


def encode_single_command(ca: int, ioa: int, close: bool, ssn: int = 0, rsn: int = 0) -> bytes:
    sco = 0x01 if close else 0x00
    asdu = bytes([TYPE_SC, 1, 6, 0]) + struct.pack("<H", ca) + _ioa(ioa) + bytes([sco])
    return _apci_i(ssn, rsn, asdu)


def encode_setpoint_float(ca: int, ioa: int, value: float, ssn: int = 0, rsn: int = 0) -> bytes:
    asdu = bytes([TYPE_SE_NC, 1, 6, 0]) + struct.pack("<H", ca) + _ioa(ioa) + struct.pack("<f", float(value)) + bytes([0])
    return _apci_i(ssn, rsn, asdu)


def _parse_ioa(buf: bytes, idx: int) -> Tuple[int, int]:
    if idx + 3 > len(buf):
        return 0, idx
    ioa = buf[idx] | (buf[idx + 1] << 8) | (buf[idx + 2] << 16)
    return ioa, idx + 3


def parse_apdu(buf: bytes) -> List[Dict[str, Any]]:
    """解析一帧 104 APDU 中的信息体"""
    if len(buf) < 6 or buf[0] != 0x68:
        return []
    if buf[1] == 4:
        return [{"u_format": buf[2]}]
    asdu = buf[6:]
    if len(asdu) < 6:
        return []
    type_id, vsq = asdu[0], asdu[1]
    ca = struct.unpack("<H", asdu[4:6])[0]
    sq = bool(vsq & 0x80)
    n = vsq & 0x7F
    idx = 6
    items = []
    ioa = 0
    for i in range(max(n, 1)):
        if not sq or i == 0:
            ioa, idx = _parse_ioa(asdu, idx)
        else:
            ioa += 1
        value = None
        if type_id in (TYPE_SP, 30) and idx < len(asdu):
            value = bool(asdu[idx] & 0x01)
            idx += 1
        elif type_id in (TYPE_ME_NB, 35) and idx + 3 <= len(asdu):
            value = struct.unpack("<h", asdu[idx:idx + 2])[0]
            idx += 3
        elif type_id in (TYPE_ME_NC, 36) and idx + 5 <= len(asdu):
            value = struct.unpack("<f", asdu[idx:idx + 4])[0]
            idx += 5
        elif type_id == 9 and idx + 3 <= len(asdu):
            value = struct.unpack("<h", asdu[idx:idx + 2])[0]
            idx += 3
        else:
            break
        items.append({"ca": ca, "ioa": ioa, "type": type_id, "value": value})
    return items


def map_points(items: List[dict], points: List[dict]) -> Dict[str, Any]:
    by_ioa = {int(p.get("ioa") or 0): p.get("name") for p in points if p.get("name")}
    out = {}
    for item in items:
        name = by_ioa.get(item.get("ioa"))
        if name and item.get("value") is not None:
            out[name] = item["value"]
    return out
