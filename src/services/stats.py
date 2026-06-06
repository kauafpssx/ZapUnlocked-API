"""Persistent runtime statistics — counters survive restarts, stored in DATA_DIR/stats.json."""

import json
import threading
from pathlib import Path

from src.config.constants import DATA_DIR

_STATS_FILE = Path(DATA_DIR) / "stats.json"
_lock = threading.Lock()

_DEFAULTS = {
    "messages_sent": 0,
    "messages_received": 0,
    "webhooks_fired": 0,
}


def _load() -> dict:
    try:
        data = json.loads(_STATS_FILE.read_text(encoding="utf-8"))
        return {k: int(data.get(k, 0)) for k in _DEFAULTS}
    except Exception:
        return dict(_DEFAULTS)


def _save(counters: dict) -> None:
    try:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(counters, indent=2), encoding="utf-8")
    except Exception:
        pass


def increment(key: str, amount: int = 1) -> None:
    with _lock:
        counters = _load()
        if key in counters:
            counters[key] += amount
            _save(counters)


def get_all() -> dict:
    with _lock:
        return _load()


def reset() -> None:
    with _lock:
        _save(dict(_DEFAULTS))
