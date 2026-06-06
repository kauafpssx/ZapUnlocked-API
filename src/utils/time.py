"""Timezone-aware timestamp utilities."""

import os
from datetime import datetime, timezone
from pathlib import Path

_BASE = Path(__file__).resolve().parents[2]
_CONF = _BASE / "timezone.conf"

_cached_tz = None
_cached_tz_name = None


def _resolve_tz_name() -> str:
    # 1. timezone.conf (first uncommented non-comment line)
    try:
        for raw in _CONF.read_text(encoding="utf-8").splitlines():
            line = raw.split("#")[0].strip()
            if line:
                return line
    except Exception:
        pass
    # 2. TZ env var (set before server start or in .env)
    name = os.environ.get("TZ", "").strip()
    if name:
        return name
    # 3. .env file direct read
    try:
        from dotenv import dotenv_values
        name = dotenv_values(_BASE / ".env").get("TZ", "").strip()
        if name:
            return name
    except Exception:
        pass
    return "UTC"


def _get_tz():
    global _cached_tz, _cached_tz_name
    tz_name = _resolve_tz_name()
    if tz_name == _cached_tz_name and _cached_tz is not None:
        return _cached_tz
    try:
        from zoneinfo import ZoneInfo
        _cached_tz = ZoneInfo(tz_name)
    except Exception:
        _cached_tz = timezone.utc
    _cached_tz_name = tz_name
    return _cached_tz


def now_ts() -> str:
    """Return current time as ISO 8601 string in the configured timezone."""
    return datetime.now(_get_tz()).strftime("%Y-%m-%dT%H:%M:%S%z")


def sent_response(res, message: str = "Message sent.") -> dict:
    """Build a standard send response including messageId and timestamp when available."""
    msg_id = getattr(res, "ID", None) if res else None
    return {
        "success": True,
        "message": message,
        "messageId": msg_id,
        "timestamp": now_ts(),
    }
