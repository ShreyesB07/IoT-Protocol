"""Helpers for Paho MQTT 2.x."""

from __future__ import annotations

import threading
import uuid

import paho.mqtt.client as mqtt


def make_mqtt_client(client_id: str | None = None) -> mqtt.Client:
    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id or f"iot-testbed-{uuid.uuid4().hex[:10]}",
        protocol=mqtt.MQTTv311,
    )


def connect_and_start(
    client: mqtt.Client,
    host: str,
    port: int,
    timeout: float = 8.0,
) -> None:
    connected = threading.Event()
    errors: list[str] = []
    previous_callback = client.on_connect

    def on_connect(_client, userdata, flags, reason_code, properties):
        if previous_callback is not None:
            previous_callback(_client, userdata, flags, reason_code, properties)
        if reason_code == 0:
            connected.set()
        else:
            errors.append(f"Broker refused connection: {reason_code}")
            connected.set()

    client.on_connect = on_connect
    client.connect(host, port, keepalive=30)
    client.loop_start()
    if not connected.wait(timeout):
        client.loop_stop()
        raise TimeoutError(f"Timed out connecting to MQTT broker at {host}:{port}")
    if errors:
        client.loop_stop()
        raise ConnectionError(errors[0])
