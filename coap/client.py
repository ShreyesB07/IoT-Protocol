"""Command-line CoAP client for the /sensor resource.

Examples:
  python -m coap.client GET
  python -m coap.client POST --data '{"temperature_c":25.1,"humidity_percent":48}'
  python -m coap.client DELETE
"""

from __future__ import annotations

import argparse
import asyncio
import json

import aiocoap


async def request_resource(host: str, port: int, method: str, data: str | None) -> None:
    protocol = await aiocoap.Context.create_client_context()
    try:
        code = getattr(aiocoap, method.upper())
        payload = b"" if data is None else data.encode("utf-8")
        request = aiocoap.Message(
            code=code,
            uri=f"coap://{host}:{port}/sensor",
            payload=payload,
        )
        response = await protocol.request(request).response
        print(f"Response code: {response.code}")
        decoded = response.payload.decode("utf-8", errors="replace")
        try:
            print(json.dumps(json.loads(decoded), indent=2))
        except json.JSONDecodeError:
            print(decoded or "<empty response>")
    finally:
        await protocol.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a CoAP request to the testbed server")
    parser.add_argument("method", choices=["GET", "POST", "PUT", "DELETE"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--data", help="JSON body for POST or PUT")
    args = parser.parse_args()
    if args.method in {"POST", "PUT"} and not args.data:
        args.data = json.dumps({
            "device_id": "coap-virtual-device-01",
            "data_origin": "SYNTHETIC_TEST_DATA",
            "temperature_c": 25.0,
            "humidity_percent": 49.0,
        })
    if args.method not in {"POST", "PUT"} and args.data:
        parser.error("--data is only used with POST or PUT")
    asyncio.run(request_resource(args.host, args.port, args.method, args.data))


if __name__ == "__main__":
    main()
