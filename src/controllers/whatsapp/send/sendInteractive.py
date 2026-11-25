"""Unified interactive/carousel controllers (Fase 5)."""

from __future__ import annotations

from fastapi import HTTPException, Request

from src.utils.phone import resolve_jid
from src.utils.decorators import handle_errors, get_session_id
from src.utils.quote import build_send_options
from src.utils.formatter import format_text
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.services.whatsapp.sender.unified_interactive import send_interactive_message, send_carousel_message
from src.schemas.interactive import SendInteractiveRequest, SendCarouselRequest


@handle_errors("send interactive")
async def send_interactive(data: SendInteractiveRequest, request: Request):
    sid = get_session_id(request)
    jid = resolve_jid(data.phone)
    options = await build_send_options(jid, reply_identifier=data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    actions = data.actions or data.buttons or []
    action_dicts = [a.model_dump(by_alias=True) if hasattr(a, "model_dump") else a for a in actions]
    body = format_text(data.body or data.text or data.message or "")
    if is_dry_run():
        return dry_run_response("Interactive message sent.")
    res = await send_interactive_message(
        jid,
        body=body,
        actions=action_dicts,
        header=data.header,
        footer=data.footer or "",
        title=data.title if hasattr(data, "title") else "",
        options=options,
        session_id=sid,
    )
    return sent_response(res, "Interactive message sent.")


@handle_errors("send carousel")
async def send_carousel(data: SendCarouselRequest, request: Request):
    sid = get_session_id(request)
    jid = resolve_jid(data.phone)
    options = await build_send_options(jid, reply_identifier=data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    cards = []
    for card in (data.cards or []):
        cd = card.model_dump(by_alias=True) if hasattr(card, "model_dump") else card
        cards.append(cd)
    if len(cards) > 10:
        raise HTTPException(status_code=400, detail={"error": "TOO_MANY_CARDS", "message": "Carousel supports at most 10 cards."})
    for card in cards:
        if len(card.get("actions") or []) > 3:
            raise HTTPException(status_code=400, detail={"error": "TOO_MANY_ACTIONS", "message": "Each carousel card supports at most 3 actions."})
    body = format_text(data.body or "")
    if is_dry_run():
        return dry_run_response("Carousel message sent.")
    res = await send_carousel_message(
        jid,
        cards=cards,
        body=body,
        footer=data.footer or "",
        options=options,
        session_id=sid,
    )
    return sent_response(res, "Carousel message sent.")