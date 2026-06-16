"""Session registry — manages WhatsApp session definitions in SQLite."""

from datetime import datetime, timezone

from src.utils.db import get_conn
from src.utils.logger import logger


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "created_at": row["created_at"],
        "active": bool(row["active"]),
    }


def _next_id() -> str:
    conn = get_conn()
    existing = {row[0] for row in conn.execute("SELECT id FROM sessions").fetchall()}
    i = 1
    while str(i) in existing:
        i += 1
    return str(i)


def ensure_default_session() -> None:
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO sessions (id, name, created_at, active) VALUES (?, ?, ?, 1)",
        ("1", "Default", _utc_now()),
    )
    conn.commit()


def list_sessions() -> list[dict]:
    conn = get_conn()
    return [_row_to_dict(r) for r in conn.execute("SELECT * FROM sessions ORDER BY id").fetchall()]


def get_session(session_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    return _row_to_dict(row) if row else None


def create_session(name: str | None = None) -> dict:
    conn = get_conn()
    new_id = _next_id()
    created = {"id": new_id, "name": name or new_id, "created_at": _utc_now(), "active": True}
    conn.execute(
        "INSERT INTO sessions (id, name, created_at, active) VALUES (?, ?, ?, 1)",
        (created["id"], created["name"], created["created_at"]),
    )
    conn.commit()
    return created


def rename_session(session_id: str, name: str) -> dict:
    conn = get_conn()
    cursor = conn.execute("UPDATE sessions SET name=? WHERE id=?", (name, session_id))
    if cursor.rowcount == 0:
        raise ValueError(f"Session '{session_id}' not found")
    conn.commit()
    return get_session(session_id)


def delete_session(session_id: str) -> None:
    conn = get_conn()
    cursor = conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    if cursor.rowcount == 0:
        raise ValueError(f"Session '{session_id}' not found")
    conn.commit()


def get_default_session_id() -> str:
    try:
        conn = get_conn()
        row = conn.execute("SELECT id FROM sessions WHERE active=1 ORDER BY id LIMIT 1").fetchone()
        return row["id"] if row else "1"
    except Exception:
        return "1"


def get_active_sessions() -> list[dict]:
    conn = get_conn()
    return [
        _row_to_dict(r)
        for r in conn.execute("SELECT * FROM sessions WHERE active=1 ORDER BY id").fetchall()
    ]
