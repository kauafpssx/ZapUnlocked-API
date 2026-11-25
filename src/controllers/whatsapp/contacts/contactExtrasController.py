"""Extra contact/business/privacy endpoints (Fase 10)."""

from __future__ import annotations

import asyncio
from typing import List

from fastapi import HTTPException, Query, Request
from pydantic import BaseModel

from src.utils.decorators import get_session_id
from src.services.whatsapp import state
from src.utils.logger import logger


class IsOnWhatsAppRequest(BaseModel):
    phones: List[str]


async def is_on_whatsapp(data: IsOnWhatsAppRequest, request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    if not data.phones:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phones' is required."})

    results = []
    for phone in data.phones[:50]:
        try:
            resp = await asyncio.wait_for(asyncio.to_thread(sock.is_on_whatsapp, phone), timeout=4.0)
            is_in = bool(resp and len(resp) > 0 and getattr(resp[0], "IsIn", False))
            jid = getattr(resp[0], "JID", None) if resp and len(resp) > 0 else None
            results.append({"phone": phone, "isOnWhatsApp": is_in, "jid": str(jid) if jid else None})
        except Exception as exc:
            logger.error(f"is_on_whatsapp failed for {phone}: {exc}")
            results.append({"phone": phone, "isOnWhatsApp": False, "jid": None, "error": str(exc)})
    return {"success": True, "results": results}


async def business_profile(phone: str = Query(...), request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    from neonize.utils import build_jid

    jid = build_jid(phone)
    try:
        bp = await asyncio.wait_for(asyncio.to_thread(sock.get_business_profile, jid), timeout=4.0)
    except Exception as exc:
        return {"success": False, "phone": phone, "businessProfile": None, "error": str(exc)}
    if not bp:
        return {"success": True, "phone": phone, "businessProfile": None}
    return {
        "success": True,
        "phone": phone,
        "businessProfile": {
            "description": getattr(bp, "Description", None),
            "category": getattr(bp, "Category", None),
            "website": getattr(bp, "Website", None),
            "email": getattr(bp, "Email", None),
        },
    }


async def user_devices(phone: str = Query(...), request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    from neonize.utils import build_jid

    jid = build_jid(phone)
    try:
        devices = await asyncio.wait_for(asyncio.to_thread(sock.get_user_devices, jid), timeout=4.0)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})
    out = []
    for d in devices or []:
        out.append({"jid": str(getattr(d, "JID", d)), "device": getattr(d, "Device", None)})
    return {"success": True, "phone": phone, "devices": out}


async def blocklist(request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    try:
        bl = await asyncio.wait_for(asyncio.to_thread(sock.get_blocklist, ""), timeout=4.0)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})
    items = []
    for entry in getattr(bl, "JIDs", []) or []:
        items.append(str(entry))
    return {"success": True, "blocklist": items}


async def privacy_settings(request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    try:
        settings = await asyncio.wait_for(asyncio.to_thread(sock.get_privacy_settings), timeout=4.0)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})
    return {"success": True, "privacy": str(settings) if settings is not None else None}