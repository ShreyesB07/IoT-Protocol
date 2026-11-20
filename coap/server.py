"""CoAP resource server exposing /sensor and /echo.

Run: python -m coap.server
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone

import aiocoap
import aiocoap.resource as resource


class SensorResource(resource.Resource):
    def __init__(self) -> None:
        super().__init__()
        self.value = {
            "device_id": "coap-virtual-device-01",
            "data_origin": "SYNTHETIC_TEST_DATA",
            "temperature_c": 24.5,
            "humidity_percent": 51.0,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    async def render_get(self, request):
        payload = json.dumps(self.value, separators=(",", ":")).encode("utf-8")
        return aiocoap.Message(code=aiocoap.CONTENT, payload=payload)

    async def render_post(self, request):
        return await self._store(request, aiocoap.CREATED)

    async def render_put(self, request):
        return await self._store(request, aiocoap.CHANGED)

    async def render_delete(self, request):
        self.value = {
            "device_id": "coap-virtual-device-01",
            "data_origin": "SYNTHETIC_TEST_DATA",
            "status": "reset",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        return aiocoap.Message(code=aiocoap.DELETED, payload=b"Sensor resource reset")

    async def _store(self, request, response_code):
        try:
            incoming = json.loads(request.payload.decode("utf-8"))
            if not isinstance(incoming, dict):
                raise ValueError("JSON body must be an object")
            self.value = {
                **incoming,
                "device_id": incoming.get("device_id", "coap-virtual-device-01"),
                "data_origin": incoming.get("data_origin", "SYNTHETIC_TEST_DATA"),
                "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            body = json.dumps(self.value, separators=(",", ":")).encode("utf-8")
            return aiocoap.Message(code=response_code, payload=body)
        except (ValueError, UnicodeDecodeError) as exc:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=str(exc).encode("utf-8"))


class EchoResource(resource.Resource):
    async def render_get(self, request):
        return aiocoap.Message(code=aiocoap.CONTENT, payload=b"CoAP echo endpoint is ready")

    async def render_post(self, request):
        return aiocoap.Message(code=aiocoap.CHANGED, payload=request.payload)


async def serve(host: str, port: int) -> None:
    root = resource.Site()
    root.add_resource(["sensor"], SensorResource())
    root.add_resource(["echo"], EchoResource())
    context = await aiocoap.Context.create_server_context(root, bind=(host, port))
    print(f"CoAP server listening at coap://{host}:{port}")
    print("Resources: /sensor (GET/POST/PUT/DELETE), /echo (GET/POST)")
    await asyncio.get_running_loop().create_future()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CoAP resource server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5683)
    args = parser.parse_args()
    try:
        asyncio.run(serve(args.host, args.port))
    except KeyboardInterrupt:
        print("\nStopping CoAP server...")


if __name__ == "__main__":
    main()
