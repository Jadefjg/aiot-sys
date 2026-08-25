"""DL/T645-2007 帧编解码（电能表抄读 / 拉合闸）"""
from typing import List, Optional, Tuple

START = 0x68
END = 0x16
CTRL_READ = 0x11
CTRL_SWITCH = 0x1C
DI_ENERGY = bytes([0x00, 0x00, 0x01, 0x00])  # 当前组合有功总电能


def _bcd_addr(text: str) -> bytes:
    digits = "".join(c for c in (text or "0") if c.isdigit()).zfill(12)[-12:]
    raw = bytes(int(digits[i:i + 2], 16) for i in range(0, 12, 2))
    return raw[::-1]


def _add33(data: bytes) -> bytes:
    return bytes((b + 0x33) & 0xFF for b in data)


def _sub33(data: bytes) -> bytes:
    return bytes((b - 0x33) & 0xFF for b in data)


def _cs(frame: bytes) -> int:
    return sum(frame) & 0xFF


def build_read(address: str, di: bytes = DI_ENERGY) -> bytes:
    addr = _bcd_addr(address)
    body = bytes([START]) + addr + bytes([START, CTRL_READ, len(di)]) + _add33(di)
    return body + bytes([_cs(body), END])


def build_switch(address: str, close_switch: bool, password: bytes = b"\x02\x00\x00\x00") -> bytes:
    """拉合闸：close_switch=True 合闸，False 拉闸"""
    addr = _bcd_addr(address)
    flag = b"\x1C" if close_switch else b"\x1A"
    data = password + flag
    body = bytes([START]) + addr + bytes([START, CTRL_SWITCH, len(data)]) + _add33(data)
    return body + bytes([_cs(body), END])


def parse_frame(data: bytes) -> Optional[Tuple[str, int, bytes]]:
    if not data:
        return None
    try:
        start = data.index(START)
    except ValueError:
        return None
    buf = data[start:]
    if len(buf) < 12 or buf[7] != START:
        return None
    length = buf[9]
    end = 10 + length + 2
    if len(buf) < end or buf[end - 1] != END:
        return None
    addr = "".join(f"{b:02X}" for b in buf[1:7][::-1])
    ctrl = buf[8]
    payload = _sub33(buf[10:10 + length])
    return addr, ctrl, payload


def decode_energy(payload: bytes) -> Optional[float]:
    """4 字节 BCD 电能，单位 0.01 kWh"""
    if len(payload) < 8:
        return None
    raw = payload[4:8][::-1]
    text = "".join(f"{b:02X}" for b in raw)
    try:
        return int(text) / 100.0
    except ValueError:
        return None


def split_frames(buffer: bytes) -> List[bytes]:
    frames = []
    i = 0
    while True:
        try:
            start = buffer.index(START, i)
        except ValueError:
            break
        if start + 10 >= len(buffer):
            break
        if buffer[start + 7] != START:
            i = start + 1
            continue
        length = buffer[start + 9]
        end = start + 10 + length + 2
        if end > len(buffer):
            break
        frames.append(buffer[start:end])
        i = end
    return frames
