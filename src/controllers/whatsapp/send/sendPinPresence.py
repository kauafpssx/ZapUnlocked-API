"""Message pin and presence controllers (Fase 7)."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel

from src.utils.phone import resolve_jid
from src.utils.decorators import handle_errors, get_session_id
from src.services.whatsapp import state
from neonize.utils import build_jid
from neonize.utils.enum import ChatPresence, ChatPresenceMedia
import asyncio


class PinMessageRequest(BaseModel):
    phone: str
    messageId: str
    sender: Optional[str] = None
    pin: bool = True
    seconds: int = 86400


class PresenceRequest(BaseModel):
    phone: str
    type: str = "composing"  # composing | recording | paused
    media: str = "text"       # text | audio


@handle_errors("pin message")
async def pin_message(data: PinMessageRequest, request: Request):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    chat_jid = build_jid(data.phone)
    if data.sender:
        sender_jid = build_jid(data.sender)
    else:
        try:
            sender_jid = sock.get_me().JID
        except Exception:
            sender_jid = chat_jid
    seconds = data.seconds if data.pin else 0
    try:
        await asyncio.to_thread(sock.pin_message, chat_jid, sender_jid, data.messageId, seconds)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})
    resp = {"success": True, "phone": data.phone, "messageId": data.messageId, "pinned": data.pin}
    if not data.pin:
        resp["warning"] = "pin_message is currently non-functional in Neonize; unpin may not take effect."
    return resp


@handle_errors("send presence")
async def send_presence(data: PresenceRequest, request: Request):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
    jid = build_jid(data.phone)
    presence_map = {"composing": ChatPresence.CHAT_PRESENCE_COMPOSING, "paused": ChatPresence.CHAT_PRESENCE_PAUSED}
    media_map = {"text": ChatPresenceMedia.CHAT_PRESENCE_MEDIA_TEXT, "audio": ChatPresenceMedia.CHAT_PRESENCE_MEDIA_AUDIO}
    if data.type not in presence_map:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": "type must be composing/paused."})
    try:
        await asyncio.to_thread(sock.send_chat_presence, jid, presence_map[data.type], media_map.get(data.media, ChatPresenceMedia.CHAT_PRESENCE_MEDIA_TEXT))
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(exc)})
    return {"success": True, "phone": data.phone, "type": data.type}