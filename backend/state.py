import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.paths import STATE_PATH


DEFAULT_STATE = {
    "people": 0,
    "risk": "LOW",
    "confidence": 0,
    "occupancy": 0,
    "alert": "Camera Offline",
    "camera": "OFFLINE",
    "updated_at": None,
}


def _offline_state(updated_at=None):
    state = DEFAULT_STATE.copy()
    state["updated_at"] = updated_at
    return state


def write_crowd_state(data, path=STATE_PATH, camera="ONLINE"):
    """Atomically replace the current detector state."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "people": int(data.get("people", 0)),
        "risk": str(data.get("risk", "LOW")),
        "confidence": float(data.get("confidence", 0)),
        "occupancy": float(data.get("occupancy", 0)),
        "alert": str(data.get("alert", "No Alert")),
        "camera": camera,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    temporary_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")

    try:
        with temporary_path.open("w", encoding="utf-8") as state_file:
            json.dump(payload, state_file)
            state_file.flush()
            os.fsync(state_file.fileno())

        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return payload


def read_crowd_state(path=STATE_PATH, max_age_seconds=10):
    """Return an online state only when a recent detector heartbeat exists."""
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as state_file:
            data = json.load(state_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        return _offline_state()

    updated_at = data.get("updated_at")

    try:
        updated = datetime.fromisoformat(updated_at)
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - updated).total_seconds()
    except (TypeError, ValueError):
        return _offline_state(updated_at)

    if data.get("camera") != "ONLINE" or age_seconds < 0 or age_seconds > max_age_seconds:
        return _offline_state(updated_at)

    try:
        return {
            "people": int(data.get("people", 0)),
            "risk": str(data.get("risk", "LOW")),
            "confidence": float(data.get("confidence", 0)),
            "occupancy": float(data.get("occupancy", 0)),
            "alert": str(data.get("alert", "No Alert")),
            "camera": "ONLINE",
            "updated_at": updated_at,
        }
    except (TypeError, ValueError):
        return _offline_state(updated_at)
