"""MQTT echo responder used by the round-trip benchmark.

Run with: python -m mqtt.echo_service
"""

from __future__ import annotations

import argparse
import json

from common.mqtt_utils import connect_and_start, make_mqtt_client

REQUEST_TOPIC = "testbed/mqtt/echo/request/+"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MQTT benchmark echo service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()

    client = make_mqtt_client("iot-testbed-mqtt-echo")

    def on_message(mqtt_client, _userdata, message):
        try:
            packet = json.loads(message.payload.decode("utf-8"))
            run_id = message.topic.rsplit("/", 1)[-1]
            response_topic = f"testbed/mqtt/echo/response/{run_id}"
            response = json.dumps(packet, separators=(",", ":")).encode("utf-8")
            # Do not block inside Paho's network callback; the loop must stay free
            # to process PUBACK/PUBCOMP packets for reliable QoS levels.
            mqtt_client.publish(response_topic, response, qos=message.qos)
            print(f"Echoed {packet.get('request_id', 'unknown')} on {response_topic}")
        except (ValueError, KeyError, UnicodeDecodeError, RuntimeError) as exc:
            print(f"Discarded malformed request: {exc}")

    client.on_message = on_message
    connect_and_start(client, args.host, args.port)
    result, _mid = client.subscribe(REQUEST_TOPIC, qos=2)
    if result != 0:
        raise RuntimeError(f"Could not subscribe to {REQUEST_TOPIC}: rc={result}")
    print(f"MQTT echo service listening on {args.host}:{args.port}")
    print(f"Request topic pattern: {REQUEST_TOPIC}")
    try:
        while True:
            __import__("time").sleep(1)
    except KeyboardInterrupt:
        print("Stopping MQTT echo service...")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
