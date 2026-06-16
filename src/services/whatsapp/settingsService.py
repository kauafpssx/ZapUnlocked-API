import json

from src.utils.db import get_conn
from src.utils.logger import logger

DEFAULT_SETTINGS = {
    "ip_control_enabled": False,
    "call_reject_auto": False,
    "call_reject_message": "I'm unavailable right now. Please send a message.",
    "auto_read_message": False,
}


def get_settings(session_id: str = "1") -> dict:
    conn = get_conn()
    rows = conn.execute(
        "SELECT key, value FROM settings WHERE session_id=?", (session_id,)
    ).fetchall()
    stored = {row["key"]: json.loads(row["value"]) for row in rows}
    return {**DEFAULT_SETTINGS, **stored}


def save_settings(settings: dict, session_id: str = "1") -> dict | None:
    try:
        conn = get_conn()
        for key, value in settings.items():
            conn.execute(
                "INSERT OR REPLACE INTO settings (session_id, key, value) VALUES (?, ?, ?)",
                (session_id, key, json.dumps(value)),
            )
        conn.commit()
        return get_settings(session_id)
    except Exception as e:
        logger.error(f"❌ Failed to save settings (session={session_id}): {e}")
        return None
