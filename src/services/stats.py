"""Persistent runtime statistics — counters survive restarts, stored per session in SQLite."""

from datetime import datetime, timezone

from src.utils.db import get_conn

_COUNTER_KEYS = ("messages_sent", "messages_received", "webhooks_fired")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def increment(key: str, amount: int = 1, session_id: str = "1") -> None:
    if key not in _COUNTER_KEYS:
        return
    conn = get_conn()
    conn.execute(
        """INSERT INTO stats (session_id, key, value) VALUES (?, ?, ?)
           ON CONFLICT(session_id, key) DO UPDATE SET value = value + excluded.value""",
        (session_id, key, amount),
    )
    conn.commit()


def increment_webhook(name: str, session_id: str = "1") -> None:
    now = _utc_now()
    conn = get_conn()
    conn.execute(
        """INSERT INTO webhook_stats (session_id, webhook_name, fired, last_fired) VALUES (?, ?, 1, ?)
           ON CONFLICT(session_id, webhook_name)
           DO UPDATE SET fired = fired + 1, last_fired = excluded.last_fired""",
        (session_id, name, now),
    )
    conn.commit()


def get_all(session_id: str = "1") -> dict:
    conn = get_conn()
    rows = conn.execute(
        "SELECT key, value FROM stats WHERE session_id=?", (session_id,)
    ).fetchall()
    result = {k: 0 for k in _COUNTER_KEYS}
    for row in rows:
        if row["key"] in result:
            result[row["key"]] = row["value"]
    return result


def get_webhook_stats(name: str = None, session_id: str = "1") -> dict:
    conn = get_conn()
    if name is not None:
        row = conn.execute(
            "SELECT fired, last_fired FROM webhook_stats WHERE session_id=? AND webhook_name=?",
            (session_id, name),
        ).fetchone()
        return {"fired": row["fired"], "last_fired": row["last_fired"]} if row else None
    rows = conn.execute(
        "SELECT webhook_name, fired, last_fired FROM webhook_stats WHERE session_id=?",
        (session_id,),
    ).fetchall()
    return {r["webhook_name"]: {"fired": r["fired"], "last_fired": r["last_fired"]} for r in rows}


def reset(session_id: str = "1") -> None:
    conn = get_conn()
    conn.execute("DELETE FROM stats WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM webhook_stats WHERE session_id=?", (session_id,))
    conn.commit()


def reset_webhook_stats(name: str = None, session_id: str = "1") -> None:
    conn = get_conn()
    if name is not None:
        conn.execute(
            "UPDATE webhook_stats SET fired=0, last_fired=NULL WHERE session_id=? AND webhook_name=?",
            (session_id, name),
        )
    else:
        conn.execute("DELETE FROM webhook_stats WHERE session_id=?", (session_id,))
    conn.commit()
