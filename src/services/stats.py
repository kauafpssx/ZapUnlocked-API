"""Persistent runtime statistics — counters survive restarts, stored in DATA_DIR/stats.json."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from src.config.constants import DATA_DIR

_STATS_FILE = Path(DATA_DIR) / "stats.json"
_lock = threading.Lock()

_DEFAULTS = {
    "messages_sent": 0,
    "messages_received": 0,
    "webhooks_fired": 0,
}


def _load_full() -> dict:
    try:
        data = json.loads(_STATS_FILE.read_text(encoding="utf-8"))
        counters = {k: int(data.get(k, 0)) for k in _DEFAULTS}
        counters["webhook_stats"] = data.get("webhook_stats", {})
        return counters
    except Exception:
        return {**_DEFAULTS, "webhook_stats": {}}


def _save(data: dict) -> None:
    try:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def increment(key: str, amount: int = 1) -> None:
    with _lock:
        data = _load_full()
        if key in _DEFAULTS:
            data[key] = data.get(key, 0) + amount
            _save(data)


def increment_webhook(name: str) -> None:
    with _lock:
        data = _load_full()
        wh = data.setdefault("webhook_stats", {})
        entry = wh.setdefault(name, {"fired": 0, "last_fired": None})
        entry["fired"] += 1
        entry["last_fired"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _save(data)


def get_all() -> dict:
    with _lock:
        d = _load_full()
        return {k: d[k] for k in _DEFAULTS}


def get_webhook_stats(name: str = None) -> dict:
    with _lock:
        data = _load_full()
        wh = data.get("webhook_stats", {})
        if name is not None:
            return wh.get(name)
        return wh


def reset() -> None:
    with _lock:
        data = _load_full()
        for k in _DEFAULTS:
            data[k] = 0
        _save(data)


def reset_webhook_stats(name: str = None) -> None:
    with _lock:
        data = _load_full()
        wh = data.setdefault("webhook_stats", {})
        if name is not None:
            if name in wh:
                wh[name] = {"fired": 0, "last_fired": None}
        else:
            data["webhook_stats"] = {}
        _save(data)
