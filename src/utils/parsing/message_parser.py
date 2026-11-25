"""Message parsing utilities for incoming WhatsApp messages.

Text/sender extraction for storage. PN/LID resolution and interactive-response
normalization are delegated to the canonical normalizer
(``src.services.whatsapp.message_normalizer``) so every consumer shares one
implementation.
"""

from src.services.whatsapp.message_normalizer import (
    normalize_native_flow_response,
    resolve_chat_jid,
)
from src.utils.logger import logger


def _safe_getattr(obj, field):
    try:
        return getattr(obj, field)
    except Exception:
        return None


def parse_message(msg) -> dict | None:
    """Parse neonize MessageEv into a standardized dict."""
    if not msg or not msg.Message:
        return None

    source = msg.Info.MessageSource

    # Centralized PN/LID resolution (single source of truth).
    resolved_jid = resolve_chat_jid(source)

    conversation_text = msg.Message.conversation or ""
    extended_text = ""
    image_caption = ""
    button_response_text = ""
    button_response_id = None

    try:
        if msg.Message.extendedTextMessage.text:
            extended_text = msg.Message.extendedTextMessage.text
    except Exception:
        pass

    try:
        if msg.Message.imageMessage.caption:
            image_caption = msg.Message.imageMessage.caption
    except Exception:
        pass

    try:
        if msg.Message.buttonsResponseMessage.selectedDisplayText:
            button_response_text = msg.Message.buttonsResponseMessage.selectedDisplayText
            button_response_id = msg.Message.buttonsResponseMessage.selectedButtonID
    except Exception:
        pass

    try:
        interactive_response = msg.Message.interactiveResponseMessage
        if interactive_response:
            flow = normalize_native_flow_response(interactive_response)
            params = flow.get("params") or {}
            button_response_id = params.get("id", "") or button_response_id
            button_response_text = params.get("display_text", button_response_text)
            if not button_response_id:
                button_response_id = _safe_getattr(
                    _safe_getattr(interactive_response, "buttonResponseMessage") or object(),
                    "selectedButtonID",
                )
                button_response_text = _safe_getattr(
                    _safe_getattr(interactive_response, "buttonResponseMessage") or object(),
                    "selectedDisplayText",
                ) or button_response_text
    except Exception:
        pass

    try:
        tbr = msg.Message.templateButtonReplyMessage
        if tbr.selectedID:
            button_response_id = tbr.selectedID
            if tbr.selectedDisplayText:
                button_response_text = tbr.selectedDisplayText
    except Exception:
        pass

    full_text = image_caption or button_response_text or extended_text or conversation_text

    context_info = None
    try:
        if msg.Message.extendedTextMessage.contextInfo.stanzaID:
            context_info = msg.Message.extendedTextMessage.contextInfo
    except Exception:
        pass

    if not context_info:
        try:
            if msg.Message.imageMessage.contextInfo.stanzaID:
                context_info = msg.Message.imageMessage.contextInfo
        except Exception:
            pass

    quoted_message = None
    if context_info:
        try:
            quoted_message = context_info.quotedMessage
        except Exception:
            pass

    return {
        "jid": resolved_jid,
        "phone": str(resolved_jid.split("@")[0]) if resolved_jid else "",
        "text": full_text,
        "imageMessage": None,
        "quotedMessage": quoted_message,
        "buttonResponse": button_response_id,
    }


def should_ignore_message(msg) -> bool:
    """Returns True if this message should be silently ignored."""
    if not msg or not msg.Message:
        return True
    if msg.Info.MessageSource.IsFromMe:
        return True
    try:
        if msg.Message.protocolMessage.type:
            return True
    except Exception:
        pass
    return False
