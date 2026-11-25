"""Order handling service: persistence, detail fetching and audit."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from src.services.whatsapp.sender.helpers import _ensure_client
from src.services.whatsapp import storage
from src.repositories import orders as order_repo
from src.services.whatsapp.message_normalizer import normalize_order
from src.utils.logger import logger


def _safe_get(obj, name, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def _details_to_items(details: Any) -> list[dict]:
    items = []
    for prod in getattr(details, "Products", []) or []:
        items.append({
            "product_id": _safe_get(prod, "ID"),
            "name": _safe_get(prod, "Name"),
            "quantity": _safe_get(prod, "Quantity"),
            "price_1000": _safe_get(prod, "Price"),
            "currency": _safe_get(prod, "Currency"),
            "image_id": _safe_get(prod, "ImageID"),
            "image_url": _safe_get(prod, "ImageURL"),
            "raw": {
                "ID": _safe_get(prod, "ID"),
                "Name": _safe_get(prod, "Name"),
                "Quantity": _safe_get(prod, "Quantity"),
                "Price": _safe_get(prod, "Price"),
                "Currency": _safe_get(prod, "Currency"),
                "ImageID": _safe_get(prod, "ImageID"),
                "ImageURL": _safe_get(prod, "ImageURL"),
            },
        })
    return items


async def persist_order_from_message(msg, phone: str, session_id: str, order_msg: Any, token: str = None) -> str:
    info = getattr(msg, "Info", None)
    message_id = getattr(info, "ID", None)
    source = getattr(info, "MessageSource", None)
    chat_jid = None
    seller_jid = None
    try:
        from src.services.whatsapp.message_normalizer import resolve_chat_jid
        chat_jid = resolve_chat_jid(source, phone)
    except Exception:
        chat_jid = phone
    try:
        seller_jid = _safe_get(order_msg, "sellerJID")
    except Exception:
        seller_jid = None
    token = token if token is not None else _safe_get(order_msg, "token")
    normalized = normalize_order(order_msg)
    order_id = normalized.get("orderId")
    if not order_id:
        return None
    order_repo.persist_order_header(
        session_id,
        order_id,
        message_id=message_id,
        chat_jid=chat_jid,
        seller_jid=seller_jid,
        whatsapp_status=normalized.get("statusName") or str(normalized.get("status")),
        local_status="received",
        currency=normalized.get("currency"),
        total_1000=normalized.get("totalAmount1000"),
        item_count=normalized.get("itemCount"),
        title=normalized.get("title"),
        note=normalized.get("message"),
        token=token,
        surface=normalized.get("surface"),
        request_message_id=normalized.get("requestMessageId"),
        catalog_type=normalized.get("catalogType"),
        raw_payload=normalized,
    )
    order_repo.add_event(
        session_id,
        order_id,
        "order.received",
        old_status=None,
        new_status=normalized.get("statusName"),
        actor="whatsapp",
        metadata={"itemCount": normalized.get("itemCount")},
    )
    return order_id


async def fetch_order_details(session_id: str, order_id: str, token: str) -> dict:
    client = _ensure_client(session_id)
    details = None
    last_error = None
    for attempt in range(3):
        try:
            details = await asyncio.wait_for(
                asyncio.to_thread(client.get_order_details, order_id, token or ""),
                timeout=10.0,
            )
            break
        except Exception as exc:
            last_error = exc
            logger.warning(f"get_order_details attempt {attempt + 1} failed: {exc}")
            await asyncio.sleep(0.5 * (attempt + 1))
    if details is None:
        try:
            from src.services.webhooks.dispatcher import dispatch_event
            await dispatch_event("order.details_failed", {
                "orderId": order_id,
                "error": str(last_error),
            }, session_id)
        except Exception:
            pass
        return {"success": False, "orderId": order_id, "error": str(last_error)}

    items = _details_to_items(details)
    order_repo.replace_order_items(session_id, order_id, items)
    order_repo.persist_order_header(
        session_id,
        order_id,
        currency=getattr(details.Price, "Currency", None) or None,
        subtotal_1000=getattr(details.Price, "Subtotal", None),
        total_1000=getattr(details.Price, "Total", None),
        item_count=len(items),
        catalog_id=getattr(details, "CatalogID", None),
        raw_payload={
            "ID": getattr(details, "ID", None),
            "CreatedAt": getattr(details, "CreatedAt", None),
            "CatalogID": getattr(details, "CatalogID", None),
            "Price": {
                "Subtotal": getattr(details.Price, "Subtotal", None),
                "Total": getattr(details.Price, "Total", None),
                "Currency": getattr(details.Price, "Currency", None),
                "PriceStatus": getattr(details.Price, "PriceStatus", None),
            },
            "Products": [i["raw"] for i in items],
        },
    )
    order_repo.add_event(
        session_id,
        order_id,
        "order.details_loaded",
        old_status=None,
        new_status="details_loaded",
        actor="system",
        metadata={"itemCount": len(items)},
    )
    try:
        from src.services.webhooks.dispatcher import dispatch_event
        await dispatch_event("order.details_loaded", {
            "orderId": order_id,
            "itemCount": len(items),
        }, session_id)
    except Exception:
        pass
    return {"success": True, "orderId": order_id, "items": items}


async def refresh_order(session_id: str, order_id: str) -> dict:
    order = order_repo.get_order(session_id, order_id)
    if not order:
        return {"success": False, "error": "ORDER_NOT_FOUND"}
    token = None
    conn_order = order_repo.get_order(session_id, order_id)
    # token not exposed by get_order; read directly
    from src.utils.db import get_conn
    row = get_conn().execute(
        "SELECT token FROM orders WHERE session_id=? AND order_id=?",
        (session_id, order_id),
    ).fetchone()
    token = row["token"] if row else None
    if not token:
        return {"success": False, "error": "TOKEN_UNAVAILABLE"}
    return await fetch_order_details(session_id, order_id, token)


def list_orders(session_id: str, **filters) -> dict:
    return order_repo.list_orders(session_id, **filters)


def get_order(session_id: str, order_id: str) -> dict | None:
    return order_repo.get_order(session_id, order_id)


async def create_order(session_id: str, data) -> dict:
    import uuid

    if isinstance(data, dict):
        payload = data
    else:
        payload = data.model_dump(exclude_none=True)
    order_id = payload.get("order_id") or payload.get("orderId") or str(uuid.uuid4())
    order_repo.persist_order_header(
        session_id,
        order_id,
        chat_jid=payload.get("chat_jid") or payload.get("chatJid"),
        seller_jid=payload.get("seller_jid") or payload.get("sellerJid"),
        whatsapp_status=payload.get("whatsapp_status"),
        local_status=payload.get("local_status") or payload.get("localStatus") or "received",
        currency=payload.get("currency") or "BRL",
        total_1000=payload.get("total_1000") or payload.get("totalAmount1000"),
        title=payload.get("title"),
        note=payload.get("note"),
        raw_payload=payload,
    )
    items = payload.get("items") or []
    if items:
        order_repo.replace_order_items(session_id, order_id, items)
    order_repo.add_event(
        session_id,
        order_id,
        "order.created",
        new_status=payload.get("local_status") or payload.get("localStatus") or "received",
        actor="api",
        metadata=payload,
    )
    return order_repo.get_order(session_id, order_id)


async def update_order(session_id: str, order_id: str, patch: dict, actor: str = "api") -> dict | None:
    existing = order_repo.get_order(session_id, order_id)
    if not existing:
        return None
    old_local = existing.get("local_status")
    new_local = patch.get("local_status", old_local)
    order_repo.update_order_local(session_id, order_id, patch, actor=actor)
    if new_local and new_local != old_local:
        order_repo.add_event(
            session_id,
            order_id,
            "order.local_status_changed",
            old_status=old_local,
            new_status=new_local,
            actor=actor,
            metadata=patch,
        )
    return order_repo.get_order(session_id, order_id)