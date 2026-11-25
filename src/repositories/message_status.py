"""Repository for message delivery/read status."""

from __future__ import annotations

from datetime import datetime, timezone

from src.utils.db import get_conn

_STATUS_RANK = {
    "failed": 0,
    "sent": 1,
    "delivered": 2,
    "read": 3,
    "played": 4,
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upsert_status(
    session_id: str,
    message_id: str,
    status: str,
    *,
    chat_jid: str | None = None,
    receipt_type: int | None = None,
    timestamp: int | None = None,
) -> None:
    if not session_id or not message_id or not status:
        return
    new_rank = _STATUS_RANK.get(status, 0)
    conn = get_conn()
    row = conn.execute(
        "SELECT status_rank FROM message_status WHERE session_id=? AND message_id=?",
        (session_id, message_id),
    ).fetchone()
    if row and new_rank < int(row["status_rank"] or 0):
        return
    now = _now()
    if row:
        conn.execute(
            """UPDATE message_status SET
                chat_jid = COALESCE(?, chat_jid),
                status = ?,
                status_rank = ?,
                receipt_type = COALESCE(?, receipt_type),
                timestamp = COALESCE(?, timestamp),
                updated_at = ?
            WHERE session_id=? AND message_id=?""",
            (chat_jid, status, new_rank, receipt_type, timestamp, now, session_id, message_id),
        )
    else:
        conn.execute(
            """INSERT INTO message_status (
                session_id, message_id, chat_jid, status, status_rank,
                receipt_type, timestamp, updated_at
            ) VALUES (?,?,?,?,?,?,?,?)""",
            (session_id, message_id, chat_jid, status, new_rank, receipt_type, timestamp, now),
        )
    conn.commit()


def get_status(session_id: str, message_id: str) -> dict | None:
    if not session_id or not message_id:
        return None
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM message_status WHERE session_id=? AND message_id=?",
        (session_id, message_id),
    ).fetchone()
    return dict(row) if row else None


def record_sent(session_id: str, message_id: str, chat_jid: str | None = None) -> None:
    upsert_status(session_id, message_id, "sent", chat_jid=chat_jid)


def record_failed(session_id: str, message_id: str, chat_jid: str | None = None) -> None:
    upsert_status(session_id, message_id, "failed", chat_jid=chat_jid)