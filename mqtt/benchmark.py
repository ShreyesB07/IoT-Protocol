"""Measure MQTT echo round-trip time against a real MQTT broker.

Run the echo service in another terminal first:
    python -m mqtt.echo_service
Then:
    python -m mqtt.benchmark --count 50 --size 64 --qos 1
"""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
import uuid

from common.metrics import record_metric
from common.mqtt_utils import connect_and_start, make_mqtt_client

REQUEST_TOPIC_PREFIX = "testbed/mqtt/echo/request"


def run_benchmark(host: str, port: int, count: int, size: int, qos: int, timeout: float) -> None:
    run_id = uuid.uuid4().hex[:10]
    response_topic = f"testbed/mqtt/echo/response/{run_id}"
    request_topic = f"{REQUEST_TOPIC_PREFIX}/{run_id}"
    client = make_mqtt_client(f"mqtt-bench-{run_id}")
    connected = threading.Event()
    subscribed = threading.Event()
    response_events: dict[str, threading.Event] = {}
    state_lock = threading.Lock()

    def on_connect(mqtt_client, _userdata, _flags, reason_code, _properties):
        if reason_code == 0:
            connected.set()
            mqtt_client.subscribe(response_topic, qos=2)
        else:
            connected.set()

    def on_subscribe(_client, _userdata, _mid, _reason_codes, _properties):
        subscribed.set()

    def on_message(_client, _userdata, message):
        try:
            packet = json.loads(message.payload.decode("utf-8"))
            with state_lock:
                event = response_events.get(packet["request_id"])
            if event is not None:
                event.set()
        except (ValueError, KeyError, UnicodeDecodeError):
            return

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    connect_and_start(client, host, port)
    if not connected.wait(5) or not subscribed.wait(5):
        client.disconnect()
        client.loop_stop()
        raise TimeoutError("MQTT benchmark could not establish its response subscription")

    payload = "x" * size
    measured: list[float] = []
    delivered = 0
    print(f"Running MQTT echo benchmark: count={count}, payload={size} B, QoS={qos}")

    try:
        for index in range(count):
            request_id = f"{run_id}-{index}"
            packet = {
                "request_id": request_id,
                "payload": payload,
            }
            encoded = json.dumps(packet, separators=(",", ":")).encode("utf-8")
            request_event = threading.Event()
            with state_lock:
                response_events[request_id] = request_event
            started = time.perf_counter_ns()
            info = client.publish(request_topic, encoded, qos=qos)
            if info.rc != 0:
                rtt = None
                success = False
                detail = f"publish_rc={info.rc}"
            else:
                try:
                    info.wait_for_publish(timeout=timeout)
                except (RuntimeError, ValueError):
                    pass
                got_response = request_event.wait(timeout)
                elapsed = (time.perf_counter_ns() - started) / 1_000_000
                success = got_response
                rtt = elapsed if success else None
                detail = "echo received" if success else "timeout waiting for echo"
            with state_lock:
                response_events.pop(request_id, None)

            if success:
                delivered += 1
                measured.append(float(rtt))
            record_metric(
                protocol="MQTT",
                experiment="echo_rtt",
                endpoint=f"{host}:{port}",
                qos=qos,
                message_size_bytes=len(encoded),
                rtt_ms=rtt,
                success=success,
                details=detail,
            )
            print(f"{index + 1:03d}/{count}: " + (f"{rtt:.3f} ms" if success else "TIMEOUT"))
    finally:
        client.disconnect()
        client.loop_stop()

    print("\nMQTT benchmark summary")
    print(f"Delivered: {delivered}/{count} ({(delivered / count * 100):.1f}%)")
    if measured:
        print(f"Mean RTT:   {statistics.mean(measured):.3f} ms")
        print(f"Median RTT: {statistics.median(measured):.3f} ms")
        print(f"Min / max:  {min(measured):.3f} / {max(measured):.3f} ms")
    print("Measurements appended to results/metrics.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure MQTT echo round-trip time")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=1883)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--size", type=int, default=64, help="Synthetic payload bytes")
    parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    if args.count < 1 or args.size < 0:
        parser.error("--count must be >= 1 and --size must be >= 0")
    run_benchmark(args.host, args.port, args.count, args.size, args.qos, args.timeout)


if __name__ == "__main__":
    main()
