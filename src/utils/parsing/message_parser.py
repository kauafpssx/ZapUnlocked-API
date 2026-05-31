"""Message parsing utilities for incoming WhatsApp messages."""

import json

from src.utils.logger import logger


def parse_message(msg) -> dict | None:
    """Parse neonize MessageEv into a standardized dict."""
    if not msg or not msg.Message:
        return None

    source = msg.Info.MessageSource
    chat = source.Chat

    resolved_user = chat.User
    jid_suffix = "@s.whatsapp.net"

    if source.IsGroup:
        jid_suffix = "@g.us"
    elif chat.Server == "lid":
        if source.SenderAlt and source.SenderAlt.Server == "s.whatsapp.net":
            resolved_user = source.SenderAlt.User
        elif source.RecipientAlt and source.RecipientAlt.Server == "s.whatsapp.net":
            resolved_user = source.RecipientAlt.User
        elif source.Sender and source.Sender.Server == "s.whatsapp.net":
            resolved_user = source.Sender.User

    conversation_text = msg.Message.conversation or ""
    extended_text = ""
    image_caption = ""
    button_response_text = ""
    button_response_id = None
    interactive_response_id = None

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
            native = interactive_response.nativeFlowResponseMessage
            if native and native.paramsJSON:
                params = json.loads(native.paramsJSON)
                interactive_response_id = params.get("id", "")
                button_response_text = params.get("display_text", button_response_text)
            elif interactive_response.buttonResponseMessage:
                button_response_id = interactive_response.buttonResponseMessage.selectedButtonID
                button_response_text = interactive_response.buttonResponseMessage.selectedDisplayText or button_response_text

            if not button_response_id:
                button_response_id = interactive_response_id
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
        "jid": f"{resolved_user}{jid_suffix}",
        "phone": str(resolved_user),
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
