"""Unified interactive and carousel senders (Fase 5)."""

from __future__ import annotations

import asyncio
import json

from src.services.whatsapp.sender.helpers import (
    _ensure_client,
    _build_context_info,
    _save_to_history,
    build_jid,
    _dispatch_sent_event,
    apply_pre_send,
)
from src.utils.logger import logger


def _action_to_button(action) -> dict:
    if hasattr(action, "model_dump"):
        action = action.model_dump(by_alias=True)
    atype = str(action.get("type", "")).lower()
    display = action.get("display_text") or action.get("text") or action.get("buttonText") or ""

    if atype in ("reply", "quick_reply"):
        return {"name": "quick_reply", "params": {"display_text": display, "id": action.get("id") or action.get("buttonId") or "reply"}}
    if atype in ("url", "cta_url"):
        return {"name": "cta_url", "params": {"display_text": display, "url": action.get("url", ""), "webview_interaction": bool(action.get("webview_interaction", False))}}
    if atype in ("copy", "cta_copy"):
        code = action.get("copy_code") or action.get("code") or ""
        return {"name": "cta_copy", "params": {"display_text": display, "copy_code": code}}
    if atype in ("call", "cta_call"):
        return {"name": "cta_call", "params": {"display_text": display, "id": action.get("phone_number") or action.get("phoneNumber") or action.get("id", "")}}
    if atype in ("reminder", "cta_reminder"):
        return {"name": "cta_reminder", "params": {"display_text": display, "id": action.get("id", "")}}
    if atype in ("cancel_reminder", "cta_cancel_reminder"):
        return {"name": "cta_cancel_reminder", "params": {"display_text": display, "id": action.get("id", "")}}
    if atype in ("address", "address_message"):
        return {"name": "address_message", "params": {"display_text": display, "id": action.get("id", "")}}
    if atype in ("location", "send_location", "location_request"):
        return {"name": "send_location", "params": action.get("extra") or {}}
    if atype in ("selection", "single_select"):
        return {"name": "single_select", "params": {"title": display or action.get("title", ""), "sections": action.get("sections") or []}}
    # Fallback: allow raw name/params
    if "name" in action:
        params = action.get("params", action.get("buttonParamsJSON", {}))
        if isinstance(params, str):
            try:
                params = __import__("json").loads(params)
            except Exception:
                params = {"value": params}
        return {"name": action["name"], "params": params or {}}
    return {"name": "quick_reply", "params": {"display_text": display or "Button", "id": action.get("id", "btn")}}


def _build_header(interactive_msg, header, client):
    if not header:
        return
    htype = str(header.get("type", "")).lower()
    if htype == "image" and header.get("url"):
        try:
            img = client.build_image_message(header["url"])
            interactive_msg.header.imageMessage.CopyFrom(img.imageMessage)
            interactive_msg.header.hasMediaAttachment = True
        except Exception as exc:
            logger.warning(f"header image load failed: {exc}")
    elif htype == "video" and header.get("url"):
        try:
            vid = client.build_video_message(header["url"])
            interactive_msg.header.videoMessage.CopyFrom(vid.videoMessage)
            if header.get("gifPlayback"):
                interactive_msg.header.videoMessage.gifPlayback = True
            interactive_msg.header.hasMediaAttachment = True
        except Exception as exc:
            logger.warning(f"header video load failed: {exc}")
    elif htype == "sticker" and header.get("url"):
        try:
            stk = client.build_sticker_message(header["url"])
            interactive_msg.header.stickerMessage.CopyFrom(stk.stickerMessage)
            interactive_msg.header.hasMediaAttachment = True
        except Exception as exc:
            logger.warning(f"header sticker load failed: {exc}")
    elif htype == "document" and header.get("url"):
        try:
            doc = client.build_document_message(header["url"])
            interactive_msg.header.documentMessage.CopyFrom(doc.documentMessage)
            interactive_msg.header.hasMediaAttachment = True
        except Exception as exc:
            logger.warning(f"header document load failed: {exc}")
    if header.get("title"):
        interactive_msg.header.title = header["title"]


async def send_interactive_message(jid, body="", actions=None, header=None, footer=None, title="", options=None, session_id="1"):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message, MessageContextInfo, InteractiveMessage, DeviceListMetadata,
    )

    client = _ensure_client(session_id)
    await apply_pre_send(jid, options, client)

    interactive_msg = InteractiveMessage()
    _build_header(interactive_msg, header, client)
    interactive_msg.body.text = body or ""
    if footer:
        interactive_msg.footer.text = footer
    if title and not interactive_msg.header.title:
        interactive_msg.header.title = title

    ci = _build_context_info(options.get("quoted") if options else None, options.get("mentioned") if options else None) if options else None
    if ci:
        interactive_msg.contextInfo.CopyFrom(ci)

    for act in (actions or []):
        btn_spec = _action_to_button(act)
        btn = interactive_msg.nativeFlowMessage.buttons.add()
        btn.name = btn_spec["name"]
        btn.buttonParamsJSON = json.dumps(btn_spec["params"], ensure_ascii=False)

    if not interactive_msg.header.title and not interactive_msg.header.hasMediaAttachment:
        interactive_msg.header.title = title or "Action Required"
    interactive_msg.nativeFlowMessage.messageVersion = 1

    msg = Message(
        interactiveMessage=interactive_msg,
        messageContextInfo=MessageContextInfo(
            deviceListMetadata=DeviceListMetadata(),
            deviceListMetadataVersion=2,
        ),
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"interactiveMessage": {"body": {"text": body}}}, res, session_id)
    await _dispatch_sent_event(jid, "interactive", res, session_id)
    return res


async def send_carousel_message(jid, cards=None, body="", footer="", options=None, session_id="1"):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message, MessageContextInfo, InteractiveMessage, DeviceListMetadata,
    )
    CarouselMessage = InteractiveMessage.CarouselMessage

    client = _ensure_client(session_id)
    await apply_pre_send(jid, options, client)

    carousel = CarouselMessage()
    carousel.messageVersion = 1
    carousel.carouselCardType = 1  # unknown, best-effort

    for card in (cards or []):
        card_interactive = InteractiveMessage()
        _build_header(card_interactive, card.get("header") if isinstance(card, dict) else getattr(card, "header", None), client)
        card_body = card.get("body") if isinstance(card, dict) else getattr(card, "body", None)
        card_footer = card.get("footer") if isinstance(card, dict) else getattr(card, "footer", None)
        card_actions = card.get("actions") if isinstance(card, dict) else getattr(card, "actions", None)
        if card_body:
            card_interactive.body.text = card_body
        if card_footer:
            card_interactive.footer.text = card_footer
        for act in (card_actions or []):
            btn_spec = _action_to_button(act)
            btn = card_interactive.nativeFlowMessage.buttons.add()
            btn.name = btn_spec["name"]
            btn.buttonParamsJSON = json.dumps(btn_spec["params"], ensure_ascii=False)
        card_interactive.nativeFlowMessage.messageVersion = 1
        carousel.cards.append(card_interactive)

    interactive_msg = InteractiveMessage()
    interactive_msg.body.text = body or ""
    if footer:
        interactive_msg.footer.text = footer
    interactive_msg.carouselMessage.CopyFrom(carousel)

    msg = Message(
        interactiveMessage=interactive_msg,
        messageContextInfo=MessageContextInfo(
            deviceListMetadata=DeviceListMetadata(),
            deviceListMetadataVersion=2,
        ),
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"interactiveMessage": {"body": {"text": body}}}, res, session_id)
    await _dispatch_sent_event(jid, "carousel", res, session_id)
    return res