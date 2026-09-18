#!/usr/bin/env python3
"""Rate-limited Redis Stream consumer for backpressure experiments."""
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
    p.add_argument("--group", default="perf-consumers")
    p.add_argument("--consumer", default="consumer-1")
    p.add_argument("--rate", type=float, default=100, help="max messages/second; 0 means unlimited")
    p.add_argument("--duration", type=int, default=30)
    p.add_argument("--create-group", action="store_true")
    args = p.parse_args()
    r = redis.Redis.from_url(args.url, decode_responses=True)
    if args.create_group:
        try:
            r.xgroup_create(args.stream, args.group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    started, consumed, last = time.monotonic(), 0, time.monotonic()
    while time.monotonic() - started < args.duration:
        batch = max(1, min(1000, int(args.rate or 1000)))
        rows = r.xreadgroup(args.group, args.consumer, {args.stream: ">"}, count=batch, block=1000)
        if not rows:
            continue
        for _, messages in rows:
            for msg_id, fields in messages:
                r.xack(args.stream, args.group, msg_id)
                consumed += 1
                if args.rate:
                    target = consumed / args.rate
                    delay = target - (time.monotonic() - last)
                    if delay > 0:
                        time.sleep(delay)
    groups = {g["name"]: g for g in r.xinfo_groups(args.stream)}
    group = groups.get(args.group, {})
    print(json.dumps({"config": vars(args), "consumed": consumed, "elapsed_seconds": round(time.monotonic() - started, 2), "stream_length": r.xlen(args.stream), "group_lag": group.get("lag"), "pending": group.get("pending", 0)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
