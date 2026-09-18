#!/usr/bin/env python3
"""Generate a controlled Redis Stream ingress rate for backpressure tests."""
import argparse
import json
import time

try:
    import redis
except ImportError as exc:  # pragma: no cover
    raise SystemExit("缺少 redis，请安装 performance/requirements.txt") from exc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="redis://127.0.0.1:6379/0")
    p.add_argument("--stream", default="iot:pipeline:telemetry")
    p.add_argument("--rate", type=float, default=1000)
    p.add_argument("--duration", type=int, default=30)
    p.add_argument("--maxlen", type=int, default=0, help="0 disables trimming")
    p.add_argument("--confirm-local", action="store_true")
    args = p.parse_args()
    if not args.confirm_local:
        raise SystemExit("写入 Stream 会改变状态，请加 --confirm-local（仅限测试 Redis）")
    r = redis.Redis.from_url(args.url, decode_responses=True)
    started, produced = time.monotonic(), 0
    while time.monotonic() - started < args.duration:
        now = time.time_ns()
        kwargs = {"maxlen": args.maxlen, "approximate": True} if args.maxlen else {}
        r.xadd(args.stream, {"device_id": f"perf-{produced % 10000}", "ts_ns": now, "payload": "{}"}, **kwargs)
        produced += 1
        target = produced / args.rate
        delay = target - (time.monotonic() - started)
        if delay > 0:
            time.sleep(delay)
    elapsed = time.monotonic() - started
    print(json.dumps({"config": vars(args), "produced": produced, "actual_rate": round(produced / elapsed, 2), "stream_length": r.xlen(args.stream)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
