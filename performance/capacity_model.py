#!/usr/bin/env python3
"""Estimate AIoT connection, throughput, bandwidth, and storage requirements.

This is a planning model, not a benchmark. Override inputs with CLI flags and
record the assumptions alongside every load-test result.
"""
import argparse
import json


def estimate(a):
    devices = a.devices
    telemetry = devices / a.telemetry_interval
    heartbeat = devices / a.heartbeat_interval
    peak_ingress = (telemetry + heartbeat) * a.peak_factor
    egress = devices * a.command_rate * a.peak_factor
    msg_bytes = a.message_bytes + a.protocol_overhead_bytes
    ingress_mbps = peak_ingress * msg_bytes * 8 / 1_000_000
    daily_bytes = telemetry * a.message_bytes * 86400
    return {
        "assumptions": vars(a),
        "average_telemetry_tps": round(telemetry, 2),
        "average_heartbeat_tps": round(heartbeat, 2),
        "peak_ingress_tps": round(peak_ingress, 2),
        "peak_command_tps": round(egress, 2),
        "peak_ingress_mbps": round(ingress_mbps, 2),
        "daily_raw_telemetry_gb": round(daily_bytes / 1e9, 2),
        "monthly_raw_telemetry_tb": round(daily_bytes * 30 / 1e12, 2),
        "broker_memory_gb_at_bytes_per_connection": round(
            devices * a.bytes_per_connection / 1e9, 2
        ),
        "recommended_broker_nodes": max(3, (devices + a.devices_per_broker - 1) // a.devices_per_broker),
        "recommended_consumers": max(1, (peak_ingress + a.tps_per_consumer - 1) // a.tps_per_consumer),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--devices", type=int, default=1_000_000)
    p.add_argument("--telemetry-interval", type=float, default=60)
    p.add_argument("--heartbeat-interval", type=float, default=60)
    p.add_argument("--command-rate", type=float, default=0.0001, help="commands/device/second")
    p.add_argument("--message-bytes", type=int, default=512)
    p.add_argument("--protocol-overhead-bytes", type=int, default=64)
    p.add_argument("--peak-factor", type=float, default=5)
    p.add_argument("--bytes-per-connection", type=int, default=20_000)
    p.add_argument("--devices-per-broker", type=int, default=250_000)
    p.add_argument("--tps-per-consumer", type=int, default=5_000)
    print(json.dumps(estimate(p.parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
