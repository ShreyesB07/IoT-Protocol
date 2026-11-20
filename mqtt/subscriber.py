"""Subscribe to virtual device telemetry and save received messages."""

from __future__ import annotations

import argparse
import json

from common.metrics import append_telemetry
from common.mqtt_utils import connect_and_start, make_mqtt_client


def main() -> None:
    parser = argparse.ArgumentParser(description="Subscribe to MQTT sensor telemetry")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--topic", default="iot/+/telemetry")
    args = parser.parse_args()

    client = make_mqtt_client("iot-testbed-telemetry-subscriber")

    def on_message(_client, _userdata, message):
        try:
            record = json.loads(message.payload.decode("utf-8"))
            record["received_topic"] = message.topic
            record["received_qos"] = message.qos
            append_telemetry(record)
            print(f"RECEIVED {message.topic}: {record}")
        except (ValueError, UnicodeDecodeError) as exc:
            print(f"Invalid telemetry message on {message.topic}: {exc}")

    client.on_message = on_message
    connect_and_start(client, args.host, args.port)
    result, _mid = client.subscribe(args.topic, qos=1)
    if result != 0:
        raise RuntimeError(f"Could not subscribe to {args.topic}: rc={result}")
    print(f"Listening for {args.topic} on {args.host}:{args.port}; Ctrl+C to stop")
    try:
        while True:
            __import__("time").sleep(1)
    except KeyboardInterrupt:
        print("\nStopping subscriber...")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
