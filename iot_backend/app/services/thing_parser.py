"""物解析：把原始 JSON / 键值 / 十六进制帧映射为物模型属性"""
from typing import Any, Dict, Optional


def _dig(data: Any, path: str):
    if not path:
        return None
    cur = data
    for part in path.lstrip("$.").replace("[", ".").replace("]", "").split("."):
        if part == "" or cur is None:
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
        else:
            return None
    return cur


def _hex_bytes(raw: str) -> bytes:
    text = "".join((raw or "").split())
    if text.lower().startswith("0x"):
        text = text[2:]
    if len(text) % 2:
        text = "0" + text
    return bytes.fromhex(text)


def _read_int(buf: bytes, offset: int, length: int, endian: str = "be") -> int:
    chunk = buf[offset:offset + length]
    if len(chunk) < length:
        return 0
    return int.from_bytes(chunk, "big" if endian != "le" else "little")


def decode_hex(raw: str, mapping: dict) -> Dict[str, Any]:
    buf = _hex_bytes(raw)
    out = {}
    for name, spec in (mapping or {}).items():
        if not isinstance(spec, dict):
            continue
        offset = int(spec.get("offset") or 0)
        length = int(spec.get("len") or spec.get("length") or 2)
        scale = float(spec.get("scale") or 1)
        endian = spec.get("endian") or "be"
        out[name] = _read_int(buf, offset, length, endian) * scale
    return out


def decode_map(payload: dict, mapping: dict) -> Dict[str, Any]:
    out = {k: v for k, v in payload.items() if k not in ("raw", "payload", "hex")}
    for src, dest in (mapping or {}).items():
        value = _dig(payload, src)
        if value is None and src in payload:
            value = payload.get(src)
        key = dest if isinstance(dest, str) else src
        if isinstance(dest, dict):
            key = dest.get("name") or src
        if value is not None:
            if src in out and src != key:
                out.pop(src, None)
            out[key] = value
    return out


def decode_kv(text: str) -> Dict[str, Any]:
    out = {}
    for part in (text or "").replace(";", ",").split(","):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        try:
            out[key] = float(val) if "." in val else int(val)
        except ValueError:
            out[key] = val
    return out


def decode_values(product, payload: Any) -> Dict[str, Any]:
    """按产品 config.parser 解析上报；无配置时尽量摊平 data 字段"""
    if payload is None:
        return {}
    parser = {}
    if product is not None:
        parser = ((product.config or {}).get("parser") or {})
    kind = (parser.get("type") or "json").lower()
    mapping = parser.get("mapping") or {}

    if isinstance(payload, str):
        text = payload.strip()
        if kind == "hex":
            return decode_hex(text, mapping)
        if kind == "kv" or ("=" in text and not text.startswith("{")):
            return decode_kv(text)
        try:
            import json
            payload = json.loads(text)
        except Exception:
            return {"message": text}

    if not isinstance(payload, dict):
        return {}
    raw = payload.get("raw") or payload.get("payload") or payload.get("hex")
    if isinstance(raw, str) and (kind == "hex" or mapping and all(isinstance(v, dict) for v in mapping.values())):
        try:
            return decode_hex(raw, mapping)
        except Exception:
            pass
    nested = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if mapping and kind in ("json", "map", ""):
        return decode_map(nested, mapping)
    return dict(nested)
