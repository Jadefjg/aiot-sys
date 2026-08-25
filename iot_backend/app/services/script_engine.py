"""边缘 JS / Lua 脚本：属性上报与定时触发，沙箱内仅暴露 write/get/log/publish"""
import logging
import re
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ScriptHost:
    def __init__(self):
        self.logs = []
        self.writes = []
        self.published = []

    def log(self, *args):
        self.logs.append(" ".join(str(a) for a in args))

    def write(self, device_id, values):
        if isinstance(values, dict) and device_id:
            self.writes.append((str(device_id), dict(values)))

    def get(self, device_id):
        from app.db.session import SessionLocal
        from app.crud.device import device_crud
        db = SessionLocal()
        try:
            device = device_crud.get_by_device_id(db, str(device_id))
            return dict(device.values or {}) if device else {}
        finally:
            db.close()

    def publish(self, topic, payload=None):
        from app.services.mqtt_service import mqtt_client
        import json
        mqtt_client.publish(str(topic), json.dumps(payload if payload is not None else {}, default=str))
        self.published.append(str(topic))


class AttrDict(dict):
    def __getattr__(self, item):
        try:
            value = self[item]
        except KeyError:
            return None
        return AttrDict(value) if isinstance(value, dict) else value


def detect_language(script) -> str:
    lang = (getattr(script, "language", None) or "").lower()
    if lang in ("js", "javascript", "lua"):
        return "lua" if lang == "lua" else "js"
    text = (getattr(script, "content", None) or "").lstrip()
    if text.startswith("--") or re.search(r"\bthen\b", text) and "end" in text:
        return "lua"
    return "js"


def lua_to_js(source: str) -> str:
    text = source or ""
    text = re.sub(r"--\[\[.*?\]\]", "", text, flags=re.S)
    text = re.sub(r"--[^\n]*", "", text)
    text = text.replace("~=", "!=")
    text = re.sub(r"\blocal\s+", "var ", text)
    text = re.sub(r"\band\b", "&&", text)
    text = re.sub(r"\bor\b", "||", text)
    text = re.sub(r"\bnot\b", "!", text)
    text = re.sub(r"\bfunction\s+(\w+)\s*\((.*?)\)", r"function \1(\2) {", text)
    text = re.sub(r"\bif\s+", "if (", text)
    text = re.sub(r"\bthen\b", ") {", text)
    text = re.sub(r"\belse\b", "} else {", text)
    text = re.sub(r"\bend\b", "}", text)
    text = re.sub(r"\bnil\b", "null", text)
    def _table(match):
        inner = re.sub(r"(\w+)\s*=", r"\1:", match.group(1))
        return "{" + inner + "}"
    text = re.sub(r"\{([^{}]*)\}", _table, text)
    return text


class _Parser:
    def __init__(self, src: str):
        self.s = src
        self.i = 0

    def peek(self):
        self._ws()
        return self.s[self.i] if self.i < len(self.s) else ""

    def _ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n;":
            self.i += 1

    def accept(self, token: str) -> bool:
        self._ws()
        if self.s.startswith(token, self.i):
            nxt = self.i + len(token)
            if token.isalpha() and nxt < len(self.s) and (self.s[nxt].isalnum() or self.s[nxt] == "_"):
                return False
            self.i = nxt
            return True
        return False


def run_js(source: str, env: Dict[str, Any]) -> ScriptHost:
    host = env.get("host") or ScriptHost()
    parser = _Parser(source or "")

    def ident():
        parser._ws()
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", parser.s[parser.i:])
        if not m:
            return None
        parser.i += m.end()
        return m.group(0)

    def value():
        parser._ws()
        if parser.accept("true"):
            return True
        if parser.accept("false"):
            return False
        if parser.accept("null"):
            return None
        if parser.peek() in ("'", '"'):
            q = parser.s[parser.i]
            parser.i += 1
            start = parser.i
            while parser.i < len(parser.s) and parser.s[parser.i] != q:
                parser.i += 1
            text = parser.s[start:parser.i]
            parser.i += 1
            return text
        m = re.match(r"-?\d+(\.\d+)?", parser.s[parser.i:])
        if m:
            parser.i += m.end()
            return float(m.group(0)) if "." in m.group(0) else int(m.group(0))
        if parser.peek() == "{":
            return object_lit()
        name = ident()
        if name is None:
            return None
        return finish_primary(resolve(name))

    def object_lit():
        parser.accept("{")
        obj = {}
        while parser.peek() and parser.peek() != "}":
            key = ident()
            parser.accept(":")
            obj[key] = expr()
            parser.accept(",")
        parser.accept("}")
        return obj

    def resolve(name):
        if name in env:
            return env[name]
        if hasattr(host, name):
            return getattr(host, name)
        return None

    def finish_primary(cur):
        while True:
            if parser.accept("."):
                key = ident()
                if isinstance(cur, dict):
                    cur = cur.get(key)
                elif cur is not None:
                    cur = getattr(cur, key, None)
                else:
                    cur = None
            elif parser.peek() == "(":
                parser.accept("(")
                args = []
                while parser.peek() and parser.peek() != ")":
                    args.append(expr())
                    parser.accept(",")
                parser.accept(")")
                if callable(cur):
                    cur = cur(*args)
                else:
                    cur = None
            else:
                break
        return cur

    def expr():
        left = value()
        parser._ws()
        for op in (">=", "<=", "==", "!=", "&&", "||", ">", "<"):
            if parser.s.startswith(op, parser.i):
                parser.i += len(op)
                right = expr()
                if op == ">":
                    return left > right
                if op == "<":
                    return left < right
                if op == ">=":
                    return left >= right
                if op == "<=":
                    return left <= right
                if op == "==":
                    return left == right
                if op == "!=":
                    return left != right
                if op == "&&":
                    return bool(left) and bool(right)
                if op == "||":
                    return bool(left) or bool(right)
        return left

    def stmt():
        if parser.accept("if"):
            parser.accept("(")
            cond = expr()
            parser.accept(")")
            parser.accept("{")
            if cond:
                while parser.peek() and parser.peek() != "}":
                    stmt()
            else:
                depth = 1
                while parser.i < len(parser.s) and depth:
                    if parser.s[parser.i] == "{":
                        depth += 1
                    elif parser.s[parser.i] == "}":
                        depth -= 1
                    parser.i += 1
                parser.i -= 1
            parser.accept("}")
            return
        if parser.accept("function"):
            ident()
            while parser.peek() and parser.peek() != "{":
                parser.i += 1
            parser.accept("{")
            depth = 1
            while parser.i < len(parser.s) and depth:
                if parser.s[parser.i] == "{":
                    depth += 1
                elif parser.s[parser.i] == "}":
                    depth -= 1
                parser.i += 1
            return
        value()

    while parser.i < len(parser.s):
        before = parser.i
        stmt()
        if parser.i == before:
            parser.i += 1
    return host


class ScriptEngine:
    def __init__(self):
        self._cache = []
        self._cache_at = 0.0
        self._last_run = {}
        self._lock = threading.Lock()
        self._tls = threading.local()

    def invalidate(self) -> None:
        self._cache_at = 0.0

    def on_device_values(self, db, device_id: str, values: dict, merged: dict) -> None:
        if getattr(self._tls, "running", False):
            return
        self._tls.running = True
        try:
            self._refresh(db)
            env_base = {
                "device_id": device_id,
                "values": AttrDict(merged or {}),
                "changed": AttrDict(values or {}),
            }
            for script in self._cache:
                if int(script.interval_seconds or 0) > 0:
                    continue
                self._run(script, env_base)
        finally:
            self._tls.running = False

    def tick(self, db) -> None:
        self._refresh(db)
        now = time.time()
        for script in self._cache:
            interval = int(script.interval_seconds or 0)
            if interval <= 0:
                continue
            last = self._last_run.get(script.id, 0)
            if now - last < interval:
                continue
            self._last_run[script.id] = now
            self._run(script, {"device_id": script.gateway_id or "", "values": AttrDict({}), "changed": AttrDict({})})

    def run_content(self, content: str, language: str = "js", device_id: str = "", values: Optional[dict] = None, apply: bool = False) -> dict:
        script = type("S", (), {"content": content, "language": language, "name": "adhoc"})()
        env = {"device_id": device_id, "values": AttrDict(values or {}), "changed": AttrDict(values or {})}
        host = self._eval(script, env)
        if apply:
            self._apply(host)
        return {"logs": host.logs, "writes": host.writes, "published": host.published}

    def _refresh(self, db) -> None:
        now = time.time()
        if now - self._cache_at > 3:
            from app.crud.group import script_crud
            self._cache = [s for s in script_crud.get_multi(db, limit=500) if s.enabled]
            self._cache_at = now

    def _run(self, script, env_base: dict) -> None:
        try:
            host = self._eval(script, dict(env_base))
            self._apply(host)
        except Exception as exc:
            logger.warning("Script %s: %s", getattr(script, "name", ""), exc)

    def _eval(self, script, env: dict) -> ScriptHost:
        host = ScriptHost()
        env = dict(env)
        env["host"] = host
        env["write"] = host.write
        env["log"] = host.log
        env["get"] = host.get
        env["publish"] = host.publish
        source = script.content or ""
        if detect_language(script) == "lua":
            source = lua_to_js(source)
        with self._lock:
            run_js(source, env)
        return host

    def _apply(self, host: ScriptHost) -> None:
        self.apply_writes(host.writes)

    def apply_writes(self, writes) -> None:
        """将脚本 write 结果落到设备（供 ACL 校验后再调用）"""
        if not writes:
            return
        from app.db.session import SessionLocal
        from app.crud.device import device_crud
        from app.services.device_runtime_service import device_runtime
        from app.services.mqtt_service import mqtt_client
        import json

        db = SessionLocal()
        try:
            for item in writes:
                if isinstance(item, (list, tuple)):
                    device_id, values = item[0], item[1]
                elif isinstance(item, dict):
                    device_id, values = item.get("device_id"), item.get("values") or {}
                else:
                    continue
                if not device_id or not values:
                    continue
                device_runtime.put_values(db, device_id, values, publish_alarm=mqtt_client._publish_alarm)
                if device_crud.get_by_device_id(db, device_id):
                    mqtt_client.publish(
                        f"device/{device_id}/write",
                        json.dumps({"device_id": device_id, "values": values}, default=str),
                    )
        finally:
            db.close()


script_engine = ScriptEngine()
