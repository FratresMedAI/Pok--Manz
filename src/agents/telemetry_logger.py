"""Opt-in local telemetry for strategy write-up evidence."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def telemetry_enabled() -> bool:
    return os.environ.get("POKEMAYNE_TELEMETRY", "0") == "1"


def telemetry_path() -> Path:
    configured = os.environ.get("POKEMAYNE_TELEMETRY_PATH", "pokemayne_telemetry.txt")
    return Path(configured)


def log_decision(event: str, payload: dict[str, Any]) -> None:
    """Append one concise JSON line when local telemetry is enabled."""
    if not telemetry_enabled():
        return
    try:
        path = telemetry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": round(time.time(), 3),
            "event": event,
            "payload": payload,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")
    except Exception:
        # Telemetry must never affect match play.
        return
