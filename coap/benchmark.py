"""Measure CoAP POST echo round-trip time against a real CoAP server."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import uuid

import aiocoap

from common.metrics import record_metric


async def run_benchmark(host: str, port: int, count: int, size: int, timeout: float) -> None:
    protocol = await aiocoap.Context.create_client_context()
    payload = "x" * size
    run_id = uuid.uuid4().hex[:10]
    measured: list[float] = []
    delivered = 0
    endpoint = f"{host}:{port}"
    print(f"Running CoAP echo benchmark: count={count}, payload={size} B")
    try:
        for index in range(count):
            body = json.dumps(
                {"request_id": f"{run_id}-{index}", "payload": payload},
                separators=(",", ":"),
            ).encode("utf-8")
            request = aiocoap.Message(
                code=aiocoap.POST,
                uri=f"coap://{host}:{port}/echo",
                payload=body,
            )
            started = time.perf_counter_ns()
            try:
                response = await asyncio.wait_for(protocol.request(request).response, timeout=timeout)
                elapsed = (time.perf_counter_ns() - started) / 1_000_000
                success = response.code == aiocoap.CHANGED and response.payload == body
                rtt = elapsed if success else None
                details = f"response={response.code}; echoed_bytes={len(response.payload)}"
            except Exception as exc:
                success = False
                rtt = None
                details = f"{type(exc).__name__}: {exc}"
            if success:
                delivered += 1
                measured.append(float(rtt))
            record_metric(
                protocol="CoAP",
                experiment="echo_rtt",
                endpoint=endpoint,
                qos="confirmable-default",
                message_size_bytes=len(body),
                rtt_ms=rtt,
                success=success,
                details=details,
            )
            print(f"{index + 1:03d}/{count}: " + (f"{rtt:.3f} ms" if success else f"FAILED ({details})"))
    finally:
        await protocol.shutdown()

    print("\nCoAP benchmark summary")
    print(f"Delivered: {delivered}/{count} ({(delivered / count * 100):.1f}%)")
    if measured:
        print(f"Mean RTT:   {statistics.mean(measured):.3f} ms")
        print(f"Median RTT: {statistics.median(measured):.3f} ms")
        print(f"Min / max:  {min(measured):.3f} / {max(measured):.3f} ms")
    print("Measurements appended to results/metrics.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure CoAP echo round-trip time")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--size", type=int, default=64, help="Echo payload bytes")
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    if args.count < 1 or args.size < 0:
        parser.error("--count must be >= 1 and --size must be >= 0")
    asyncio.run(run_benchmark(args.host, args.port, args.count, args.size, args.timeout))


if __name__ == "__main__":
    main()
