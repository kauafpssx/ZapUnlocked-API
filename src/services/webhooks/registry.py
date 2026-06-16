import json
import re
from datetime import datetime, timezone

from src.utils.db import get_conn
from src.utils.logger import logger

ALL_EVENTS = [
    # ── Message received ──────────────────────────────────────
    "message.text",
    "message.image",
    "message.video",
    "message.audio",
    "message.document",
    "message.sticker",
    "message.contact",
    "message.contacts",
    "message.location",
    "message.reaction",
    "message.poll_created",
    "message.poll_vote",
    "message.button_reply",
    "message.list_reply",
    "message.deleted",
    "message.unknown",
    "message.undecryptable",
    # ── Message sent ──────────────────────────────────────────
    "message.sent",
    "message.delivered",
    "message.read",
    "message.receipt",
    # ── Connection lifecycle ──────────────────────────────────
    "connection.connected",
    "connection.disconnected",
    "connection.qr_ready",
    "connection.pair_code",
    "connection.pair_status",
    "connection.logged_out",
    "connection.connect_failure",
    "connection.stream_error",
    "connection.temporary_ban",
    "connection.client_outdated",
    "connection.stream_replaced",
    # ── Group events ──────────────────────────────────────────
    "group.join",
    "group.update",
    # ── Contact / Presence ────────────────────────────────────
    "contact.presence",
    "contact.chat_presence",
    "contact.picture_change",
    "contact.identity_change",
    # ── Call events ───────────────────────────────────────────
    "call.received",
    "call.accepted",
    "call.terminated",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "-", name).strip("-")
    return slug[:64]


def _row_to_dict(row) -> dict:
    wh = {
        "name": row["name"],
        "url": row["url"],
        "method": row["method"],
        "headers": json.loads(row["headers"]),
        "body": json.loads(row["body"]),
        "events": json.loads(row["events"]),
        "active": bool(row["active"]),
        "created_at": row["created_at"],
    }
    if row["secret"]:
        wh["secret"] = row["secret"]
    return wh


def list_webhooks(session_id: str = "1") -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM webhooks WHERE session_id=? ORDER BY name", (session_id,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_webhook(name: str, session_id: str = "1") -> dict | None:
    slug = _slugify(name)
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM webhooks WHERE session_id=? AND name=?", (session_id, slug)
    ).fetchone()
    return _row_to_dict(row) if row else None


def create_webhook(data: dict, session_id: str = "1") -> dict:
    name = _slugify(data.get("name", ""))
    if not name:
        raise ValueError("'name' is required.")
    conn = get_conn()
    if conn.execute(
        "SELECT 1 FROM webhooks WHERE session_id=? AND name=?", (session_id, name)
    ).fetchone():
        raise ValueError(f"Webhook '{name}' already exists. Use PUT to update.")

    wh = {
        "name": name,
        "url": data["url"],
        "method": data.get("method", "POST"),
        "headers": data.get("headers", {}),
        "body": data.get("body", {}),
        "events": data.get("events", ["*"]),
        "active": data.get("active", True),
        "created_at": data.get("created_at") or _utc_now(),
        "secret": data.get("secret"),
    }
    conn.execute(
        """INSERT INTO webhooks
               (session_id, name, url, method, headers, body, events, active, created_at, secret)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id, wh["name"], wh["url"], wh["method"],
            json.dumps(wh["headers"]), json.dumps(wh["body"]), json.dumps(wh["events"]),
            1 if wh["active"] else 0, wh["created_at"], wh["secret"],
        ),
    )
    conn.commit()
    logger.info(f"🔗 Webhook created: {name} (session={session_id})")
    result = {k: v for k, v in wh.items() if k != "secret" or v}
    return result


def update_webhook(name: str, data: dict, session_id: str = "1") -> dict:
    slug = _slugify(name)
    wh = get_webhook(slug, session_id)
    if not wh:
        raise ValueError(f"Webhook '{slug}' not found.")

    if "url" in data:
        wh["url"] = data["url"]
    if "method" in data:
        wh["method"] = data["method"]
    if "headers" in data and data["headers"] is not None:
        wh["headers"] = data["headers"]
    if "body" in data and data["body"] is not None:
        wh["body"] = data["body"]
    if "events" in data and data["events"] is not None:
        wh["events"] = data["events"]
    if "active" in data and data["active"] is not None:
        wh["active"] = data["active"]
    if "secret" in data:
        if data["secret"]:
            wh["secret"] = data["secret"]
        else:
            wh.pop("secret", None)

    conn = get_conn()
    conn.execute(
        """UPDATE webhooks
           SET url=?, method=?, headers=?, body=?, events=?, active=?, secret=?
           WHERE session_id=? AND name=?""",
        (
            wh["url"], wh["method"],
            json.dumps(wh["headers"]), json.dumps(wh["body"]), json.dumps(wh["events"]),
            1 if wh.get("active", True) else 0, wh.get("secret"),
            session_id, slug,
        ),
    )
    conn.commit()
    logger.info(f"🔗 Webhook updated: {slug} (session={session_id})")
    return wh


def delete_webhook(name: str, session_id: str = "1") -> None:
    slug = _slugify(name)
    conn = get_conn()
    cursor = conn.execute(
        "DELETE FROM webhooks WHERE session_id=? AND name=?", (session_id, slug)
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Webhook '{slug}' not found.")
    conn.commit()
    logger.info(f"🗑️ Webhook removed: {slug} (session={session_id})")


def toggle_webhook(name: str, active: bool, session_id: str = "1") -> dict:
    slug = _slugify(name)
    conn = get_conn()
    cursor = conn.execute(
        "UPDATE webhooks SET active=? WHERE session_id=? AND name=?",
        (1 if active else 0, session_id, slug),
    )
    if cursor.rowcount == 0:
        raise ValueError(f"Webhook '{slug}' not found.")
    conn.commit()
    status = "enabled" if active else "disabled"
    logger.info(f"🔗 Webhook {status}: {slug} (session={session_id})")
    return get_webhook(slug, session_id)


def get_active_webhooks_for_event(event_type: str, session_id: str = "1") -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM webhooks WHERE session_id=? AND active=1", (session_id,)
    ).fetchall()
    result = []
    for row in rows:
        events = json.loads(row["events"])
        if "*" in events or event_type in events:
            result.append(_row_to_dict(row))
    return result
