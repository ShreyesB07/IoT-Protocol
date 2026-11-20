"""Thread-safe CSV logging for measured protocol experiments."""

from __future__ import annotations

import csv
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.paths import METRICS_FILE

_FIELDS = [
    "timestamp_utc",
    "protocol",
    "experiment",
    "endpoint",
    "qos",
    "message_size_bytes",
    "rtt_ms",
    "success",
    "details",
]
_LOCK = threading.Lock()


def record_metric(
    *,
    protocol: str,
    experiment: str,
    endpoint: str,
    qos: str | int = "n/a",
    message_size_bytes: int = 0,
    rtt_ms: float | None = None,
    success: bool,
    details: str = "",
    output_file: Path = METRICS_FILE,
) -> None:
    """Append one measurement row. RTT is None when a request timed out."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    row: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "protocol": protocol.upper(),
        "experiment": experiment,
        "endpoint": endpoint,
        "qos": qos,
        "message_size_bytes": int(message_size_bytes),
        "rtt_ms": "" if rtt_ms is None else round(float(rtt_ms), 4),
        "success": bool(success),
        "details": details.replace("\n", " "),
    }
    with _LOCK:
        write_header = not output_file.exists() or output_file.stat().st_size == 0
        with output_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)


def append_telemetry(record: dict[str, Any]) -> None:
    """Append a received telemetry message as JSON Lines."""
    import json

    from common.paths import TELEMETRY_FILE

    with _LOCK:
        with TELEMETRY_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
