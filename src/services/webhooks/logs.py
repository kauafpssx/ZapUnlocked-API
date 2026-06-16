"""Webhook dispatch log — persists last N delivery attempts per webhook in SQLite."""

from datetime import datetime, timezone

from src.utils.db import get_conn

_MAX_PER_WEBHOOK = 100


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_dispatch(
    webhook_name: str,
    event: str,
    status_code: int | None,
    success: bool,
    error: str | None = None,
    session_id: str = "1",
) -> None:
    conn = get_conn()
    conn.execute(
        """INSERT INTO webhook_logs
               (session_id, webhook_name, timestamp, event, status_code, success, error)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (session_id, webhook_name, _utc_now(), event, status_code, 1 if success else 0, error),
    )
    # Keep only the most recent _MAX_PER_WEBHOOK entries per webhook
    conn.execute(
        """DELETE FROM webhook_logs
           WHERE session_id=? AND webhook_name=? AND id NOT IN (
               SELECT id FROM webhook_logs
               WHERE session_id=? AND webhook_name=?
               ORDER BY id DESC LIMIT ?
           )""",
        (session_id, webhook_name, session_id, webhook_name, _MAX_PER_WEBHOOK),
    )
    conn.commit()


def get_logs(webhook_name: str, limit: int = 50, session_id: str = "1") -> list:
    conn = get_conn()
    rows = conn.execute(
        """SELECT timestamp, event, status_code, success, error
           FROM webhook_logs
           WHERE session_id=? AND webhook_name=?
           ORDER BY id DESC LIMIT ?""",
        (session_id, webhook_name, limit),
    ).fetchall()
    return [
        {
            "timestamp": row["timestamp"],
            "event": row["event"],
            "statusCode": row["status_code"],
            "success": bool(row["success"]),
            "error": row["error"],
        }
        for row in rows
    ]


def delete_logs(webhook_name: str | None = None, session_id: str = "1") -> None:
    conn = get_conn()
    if webhook_name:
        conn.execute(
            "DELETE FROM webhook_logs WHERE session_id=? AND webhook_name=?",
            (session_id, webhook_name),
        )
    else:
        conn.execute("DELETE FROM webhook_logs WHERE session_id=?", (session_id,))
    conn.commit()
