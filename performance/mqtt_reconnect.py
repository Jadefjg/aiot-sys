#!/usr/bin/env python3
"""Controlled MQTT connection/reconnect storm generator (local test only)."""
import argparse
import json
import random
import threading
import time

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 paho-mqtt，请安装 performance/requirements.txt") from exc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--clients", type=int, default=10)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--hold-seconds", type=float, default=5)
    p.add_argument("--jitter-ms", type=int, default=100)
    p.add_argument("--confirm-local", action="store_true", help="required safety acknowledgement")
    args = p.parse_args()
    if not args.confirm_local:
        raise SystemExit("批量连接/断开是有影响的操作，请加 --confirm-local（仅限测试 Broker）")
    clients, stats, lock = [], {"connect_ok": 0, "connect_fail": 0, "disconnect": 0, "reconnect_error": 0}, threading.Lock()

    def on_connect(client, userdata, flags, rc, properties=None):
        with lock:
            stats["connect_ok" if rc == 0 else "connect_fail"] += 1

    for i in range(args.clients):
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"load-reconnect-{i}-{random.randint(1, 10**9)}")
        c.on_connect = on_connect
        c.connect_async(args.host, args.port, 30)
        c.loop_start()
        clients.append(c)
        time.sleep(args.jitter_ms / 1000)
    time.sleep(args.hold_seconds)
    started = time.monotonic()
    for r in range(args.rounds):
        for c in clients:
            c.disconnect()
            c.loop_stop()
            with lock:
                stats["disconnect"] += 1
        time.sleep(max(0.05, args.jitter_ms / 1000))
        for c in clients:
            try:
                c.connect_async(args.host, args.port, 30)
                c.loop_start()
            except Exception:
                with lock:
                    stats["reconnect_error"] += 1
        time.sleep(args.hold_seconds)
    elapsed = time.monotonic() - started
    for c in clients:
        c.loop_stop()
        c.disconnect()
    expected = args.clients * (args.rounds + 1)
    print(json.dumps({"config": vars(args), "elapsed_seconds": round(elapsed, 2), "expected_connects": expected, "connect_success_rate": round(stats["connect_ok"] / expected, 4), "stats": stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
