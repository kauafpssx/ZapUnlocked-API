"""Payment senders (Fase 4)."""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from src.services.whatsapp.sender.native_flow import send_native_flow_message
from src.repositories import orders as order_repo
from src.utils.logger import logger


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_reference_id(session_id: str, order_id: str | None, amount_1000: int, currency: str) -> str:
    seed = f"{session_id}|{order_id or ''}|{amount_1000}|{currency}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _persist_reference(session_id: str, reference_id: str, order_id: str | None, amount_1000: int, currency: str, pix_key_type: str, pix_key: str) -> None:
    from src.utils.db import get_conn

    key_hash = hashlib.sha256(pix_key.encode("utf-8")).hexdigest()
    conn = get_conn()
    conn.execute(
        """INSERT INTO payment_references (session_id, reference_id, order_id, amount_1000, currency, pix_key_type, pix_key_hash, created_at)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(session_id, reference_id) DO NOTHING""",
        (session_id, reference_id, order_id, amount_1000, currency, pix_key_type, key_hash, _now()),
    )
    conn.commit()


async def send_payment_info(session_id: str, jid: str, data) -> object:
    payload = data.model_dump(exclude_none=True) if hasattr(data, "model_dump") else dict(data)
    reference_id = payload.get("reference_id") or payload.get("referenceId") or generate_reference_id(
        session_id, payload.get("order_id") or payload.get("orderId"), payload["amount_1000"], payload.get("currency", "BRL")
    )
    params = {
        "reference_id": reference_id,
        "type": "payment_info",
        "amount": {"value": payload["amount_1000"], "offset": payload.get("offset", 100)},
        "currency": payload.get("currency", "BRL"),
        "payment_settings": [
            {
                "type": "pix_static_code",
                "pix_static_code": {
                    "merchant_name": payload["merchant_name"],
                    "key": payload["pix_key"],
                    "key_type": payload.get("pix_key_type", "EVP"),
                    "city": payload.get("city") or "Brasil",
                    "description": payload.get("description") or "",
                },
            }
        ],
    }
    _persist_reference(
        session_id,
        reference_id,
        payload.get("order_id") or payload.get("orderId"),
        payload["amount_1000"],
        payload.get("currency", "BRL"),
        payload.get("pix_key_type", "EVP"),
        payload["pix_key"],
    )
    res = await send_native_flow_message(
        jid,
        payload.get("body") or "Informações de pagamento",
        buttons=[{"name": "payment_info", "params": params}],
        title=payload.get("title") or "",
        footer=payload.get("footer") or "",
        version=1,
        session_id=session_id,
    )
    return res, reference_id


async def send_review_and_pay(session_id: str, jid: str, data) -> object:
    payload = data.model_dump(exclude_none=True) if hasattr(data, "model_dump") else dict(data)
    reference_id = payload.get("reference_id") or payload.get("referenceId") or generate_reference_id(
        session_id, payload.get("order_id") or payload.get("orderId"), payload["amount_1000"], payload.get("currency", "BRL")
    )
    params = {
        "reference_id": reference_id,
        "type": "physical-goods",
        "payment_configuration": "merchant_categorization_code",
        "currency": payload.get("currency", "BRL"),
        "total_amount": {"value": payload["amount_1000"], "offset": payload.get("offset", 100)},
        "payment_settings": [
            {
                "type": "pix_static_code",
                "pix_static_code": {
                    "merchant_name": payload["merchant_name"],
                    "key": payload["pix_key"],
                    "key_type": payload.get("pix_key_type", "EVP"),
                    "city": payload.get("city") or "Brasil",
                    "description": payload.get("description") or "",
                },
            }
        ],
    }
    _persist_reference(
        session_id,
        reference_id,
        payload.get("order_id") or payload.get("orderId"),
        payload["amount_1000"],
        payload.get("currency", "BRL"),
        payload.get("pix_key_type", "EVP"),
        payload["pix_key"],
    )
    res = await send_native_flow_message(
        jid,
        payload.get("body") or "Revise e pague",
        buttons=[{"name": "review_and_pay", "params": params}],
        title=payload.get("title") or "",
        footer=payload.get("footer") or "",
        version=1,
        session_id=session_id,
    )
    return res, reference_id