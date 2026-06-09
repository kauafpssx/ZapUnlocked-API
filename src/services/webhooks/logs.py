"""Webhook dispatch log — persists last N delivery attempts per webhook."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from src.config.constants import DATA_DIR

_LOGS_FILE = Path(DATA_DIR) / "webhook_logs.json"
_MAX_PER_WEBHOOK = 100
_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load() -> dict:
    try:
        if _LOGS_FILE.exists():
            return json.loads(_LOGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save(data: dict):
    _LOGS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def record_dispatch(webhook_name: str, event: str, status_code: int | None, success: bool, error: str | None = None):
    """Append a delivery attempt to the in-memory + on-disk log for a webhook."""
    entry = {
        "timestamp": _utc_now(),
        "event": event,
        "statusCode": status_code,
        "success": success,
        "error": error,
    }
    with _lock:
        data = _load()
        logs = data.get(webhook_name, [])
        logs.append(entry)
        # keep only last N
        if len(logs) > _MAX_PER_WEBHOOK:
            logs = logs[-_MAX_PER_WEBHOOK:]
        data[webhook_name] = logs
        _save(data)


def get_logs(webhook_name: str, limit: int = 50) -> list:
    with _lock:
        data = _load()
    logs = data.get(webhook_name, [])
    return list(reversed(logs))[:limit]


def delete_logs(webhook_name: str | None = None):
    with _lock:
        if webhook_name:
            data = _load()
            data.pop(webhook_name, None)
            _save(data)
        else:
            _save({})
