"""Publish clearly labelled synthetic IoT telemetry over real MQTT.

Run: python -m mqtt.device --device-id room-01 --count 10
Sensor values are generated for protocol testing; they are NOT real measurements.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone

from common.mqtt_utils import connect_and_start, make_mqtt_client


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish synthetic sensor telemetry over MQTT")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--device-id", default="virtual-room-01")
    parser.add_argument("--count", type=int, default=10, help="0 means run until stopped")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    if args.count < 0 or args.interval < 0:
        parser.error("--count and --interval must be non-negative")

    rng = random.Random(args.seed)
    client = make_mqtt_client(f"device-{args.device_id}")
    connect_and_start(client, args.host, args.port)
    topic = f"iot/{args.device_id}/telemetry"
    print(f"Publishing SYNTHETIC telemetry to {topic}; Ctrl+C to stop")
    index = 0
    try:
        while args.count == 0 or index < args.count:
            sample = {
                "device_id": args.device_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "data_origin": "SYNTHETIC_TEST_DATA",
                "temperature_c": round(rng.uniform(18.0, 32.0), 2),
                "humidity_percent": round(rng.uniform(30.0, 75.0), 2),
            }
            info = client.publish(topic, json.dumps(sample), qos=args.qos)
            info.wait_for_publish(timeout=5)
            index += 1
            print(f"{index}: {sample}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping publisher...")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
