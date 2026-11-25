"""Idempotent repository for orders, items and audit events."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src.utils.db import get_conn


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_json(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            json.loads(value)
            return value
        except (ValueError, TypeError):
            return json.dumps({"value": value}, ensure_ascii=False)
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"repr": repr(value)}, ensure_ascii=False)


def persist_order_header(
    session_id: str,
    order_id: str,
    *,
    message_id: str = None,
    chat_jid: str = None,
    seller_jid: str = None,
    whatsapp_status: str = None,
    local_status: str = None,
    currency: str = None,
    subtotal_1000: int = None,
    total_1000: int = None,
    item_count: int = None,
    title: str = None,
    note: str = None,
    token: str = None,
    catalog_id: str = None,
    surface: str = None,
    request_message_id: str = None,
    raw_payload=None,
) -> str:
    if not order_id:
        return None
    conn = get_conn()
    existing = conn.execute(
        "SELECT order_id, token FROM orders WHERE session_id=? AND order_id=?",
        (session_id, order_id),
    ).fetchone()
    now = _now()
    raw = _safe_json(raw_payload)
    if existing:
        conn.execute(
            """UPDATE orders SET
                message_id = COALESCE(?, message_id),
                chat_jid = COALESCE(?, chat_jid),
                seller_jid = COALESCE(?, seller_jid),
                whatsapp_status = COALESCE(?, whatsapp_status),
                local_status = COALESCE(?, local_status),
                currency = COALESCE(?, currency),
                subtotal_1000 = COALESCE(?, subtotal_1000),
                total_1000 = COALESCE(?, total_1000),
                item_count = COALESCE(?, item_count),
                title = COALESCE(?, title),
                note = COALESCE(?, note),
                token = COALESCE(?, token),
                catalog_id = COALESCE(?, catalog_id),
                surface = COALESCE(?, surface),
                request_message_id = COALESCE(?, request_message_id),
                raw_payload = COALESCE(?, raw_payload),
                updated_at = ?
            WHERE session_id=? AND order_id=?""",
            (
                message_id, chat_jid, seller_jid, whatsapp_status, local_status,
                currency, subtotal_1000, total_1000, item_count, title, note,
                token, catalog_id, surface, request_message_id, raw, now,
                session_id, order_id,
            ),
        )
    else:
        conn.execute(
            """INSERT INTO orders (
                session_id, order_id, message_id, chat_jid, seller_jid,
                whatsapp_status, local_status, currency, subtotal_1000, total_1000,
                item_count, title, note, token, catalog_id, surface,
                request_message_id, raw_payload, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id, order_id, message_id, chat_jid, seller_jid,
                whatsapp_status, local_status or "received", currency, subtotal_1000,
                total_1000, item_count, title, note, token, catalog_id, surface,
                request_message_id, raw, now, now,
            ),
        )
    conn.commit()
    return order_id


def replace_order_items(session_id: str, order_id: str, items: list) -> None:
    conn = get_conn()
    conn.execute(
        "DELETE FROM order_items WHERE session_id=? AND order_id=?",
        (session_id, order_id),
    )
    for item in items or []:
        conn.execute(
            """INSERT INTO order_items (
                session_id, order_id, product_id, name, quantity, price_1000,
                currency, image_id, image_url, raw_payload
            ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                session_id, order_id,
                item.get("product_id") or item.get("productId") or item.get("ID"),
                item.get("name") or item.get("Name"),
                item.get("quantity") or item.get("Quantity"),
                item.get("price_1000") if item.get("price_1000") is not None else item.get("Price"),
                item.get("currency") or item.get("Currency"),
                item.get("image_id") or item.get("ImageID"),
                item.get("image_url") or item.get("ImageURL"),
                _safe_json(item.get("raw") or item),
            ),
        )
    conn.commit()


def get_order(session_id: str, order_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM orders WHERE session_id=? AND order_id=?",
        (session_id, order_id),
    ).fetchone()
    if not row:
        return None
    order = dict(row)
    # Never expose token.
    order.pop("token", None)
    items = conn.execute(
        "SELECT * FROM order_items WHERE session_id=? AND order_id=?",
        (session_id, order_id),
    ).fetchall()
    order["items"] = [dict(r) for r in items]
    events = conn.execute(
        "SELECT * FROM order_events WHERE session_id=? AND order_id=? ORDER BY id",
        (session_id, order_id),
    ).fetchall()
    order["events"] = [dict(r) for r in events]
    # Parse raw_payload
    for key in ("raw_payload",):
        if order.get(key):
            try:
                order[key] = json.loads(order[key])
            except (ValueError, TypeError):
                pass
    for item in order["items"]:
        if item.get("raw_payload"):
            try:
                item["raw_payload"] = json.loads(item["raw_payload"])
            except (ValueError, TypeError):
                pass
    for ev in order["events"]:
        if ev.get("metadata"):
            try:
                ev["metadata"] = json.loads(ev["metadata"])
            except (ValueError, TypeError):
                pass
    return order


def list_orders(
    session_id: str,
    *,
    phone: str = None,
    status: str = None,
    currency: str = None,
    date_from: str = None,
    date_to: str = None,
    local_status: str = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    conn = get_conn()
    clauses = ["session_id=?"]
    params: list = [session_id]
    if phone:
        clauses.append("(chat_jid LIKE ? OR seller_jid LIKE ?)")
        params.extend([f"%{phone}%", f"%{phone}%"])
    if status:
        clauses.append("whatsapp_status=?")
        params.append(status)
    if local_status:
        clauses.append("local_status=?")
        params.append(local_status)
    if currency:
        clauses.append("currency=?")
        params.append(currency)
    if date_from:
        clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("created_at <= ?")
        params.append(date_to)
    where = " AND ".join(clauses)
    total = conn.execute(f"SELECT COUNT(*) FROM orders WHERE {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM orders WHERE {where} ORDER BY created_at DESC, order_id DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()
    orders = []
    for row in rows:
        o = dict(row)
        o.pop("token", None)
        orders.append(o)
    return {"total": total, "limit": limit, "offset": offset, "orders": orders}


def update_order_local(session_id: str, order_id: str, patch: dict, actor: str = "api") -> dict | None:
    existing = get_order(session_id, order_id)
    if not existing:
        return None
    conn = get_conn()
    now = _now()
    fields = []
    values = []
    mapping = {
        "local_status": "local_status",
        "quantity": None,
        "price": None,
        "discount": None,
        "shipping": None,
        "note": "note",
    }
    # Generic supported columns.
    allowed = {"local_status", "note", "title"}
    for key, col in (("local_status", "local_status"), ("note", "note"), ("title", "title")):
        if key in patch and patch[key] is not None:
            fields.append(f"{col}=?")
            values.append(patch[key])
    if fields:
        values.extend([now, session_id, order_id])
        conn.execute(
            f"UPDATE orders SET {', '.join(fields)}, updated_at=? WHERE session_id=? AND order_id=?",
            values,
        )
    # Store extra adjustments in metadata event.
    conn.commit()
    return get_order(session_id, order_id)


def add_event(session_id: str, order_id: str, event_type: str, old_status=None, new_status=None, actor: str = "system", metadata=None) -> None:
    conn = get_conn()
    conn.execute(
        """INSERT INTO order_events (session_id, order_id, event_type, old_status, new_status, actor, metadata, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (session_id, order_id, event_type, old_status, new_status, actor, _safe_json(metadata), _now()),
    )
    conn.commit()


def discard_token(session_id: str, order_id: str) -> None:
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET token=NULL, updated_at=? WHERE session_id=? AND order_id=?",
        (_now(), session_id, order_id),
    )
    conn.commit()