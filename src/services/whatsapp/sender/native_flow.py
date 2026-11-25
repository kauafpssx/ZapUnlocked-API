"""Sender for WhatsApp native-flow (InteractiveMessage) messages."""

from __future__ import annotations

import json

from src.services.whatsapp.sender.helpers import (
    _ensure_client,
    _build_context_info,
    _save_to_history,
    build_jid,
    _dispatch_sent_event,
    apply_pre_send,
)
from src.services.whatsapp import storage
from src.utils.logger import logger


async def send_native_flow_message(
    jid: str,
    text: str = "",
    buttons: list = None,
    options: dict = None,
    title: str = "",
    footer: str = "",
    version: int = 1,
    message_params=None,
    message_params_json: str = None,
    image_url: str = None,
    session_id: str = "1",
    **kwargs,
):
    # Accept aliases / alternate call styles.
    if buttons is None and "buttons" in kwargs:
        buttons = kwargs.pop("buttons")
    if options is None and "options" in kwargs:
        options = kwargs.pop("options")
    if "messageParams" in kwargs:
        message_params = kwargs.pop("messageParams")
    if "messageParamsJSON" in kwargs:
        message_params_json = kwargs.pop("messageParamsJSON")
    if "sessionId" in kwargs:
        session_id = kwargs.pop("sessionId")
    if "session_id" in kwargs:
        session_id = kwargs.pop("session_id")
    if "body" in kwargs and not text:
        text = kwargs.pop("body")
    if "footer" in kwargs and not footer:
        footer = kwargs.pop("footer")
    if "title" in kwargs and not title:
        title = kwargs.pop("title")
    if "version" in kwargs:
        version = kwargs.pop("version")

    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message,
        MessageContextInfo,
        InteractiveMessage,
        DeviceListMetadata,
    )

    client = _ensure_client(session_id)
    await apply_pre_send(jid, options, client)

    interactive_msg = InteractiveMessage()

    if image_url:
        interactive_msg.header.hasMediaAttachment = True
        try:
            img_full = client.build_image_message(image_url)
            interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)
        except Exception as e:
            logger.warning(f"Failed to load image for header: {e}")
            interactive_msg.header.hasMediaAttachment = False
            if title:
                interactive_msg.header.title = title
    elif title:
        interactive_msg.header.title = title
        interactive_msg.header.hasMediaAttachment = False

    interactive_msg.body.text = text or ""

    ci = _build_context_info(
        options.get("quoted") if options else None,
        options.get("mentioned") if options else None,
    ) if options else None
    if ci:
        interactive_msg.contextInfo.CopyFrom(ci)

    if footer:
        interactive_msg.footer.text = footer

    # Serialize message-level params exactly once.
    if message_params_json is not None:
        serialized_message_params = message_params_json
    elif message_params is not None:
        if isinstance(message_params, str):
            try:
                json.loads(message_params)
                serialized_message_params = message_params
            except (ValueError, TypeError):
                serialized_message_params = json.dumps({"value": message_params}, ensure_ascii=False)
        else:
            serialized_message_params = json.dumps(message_params, ensure_ascii=False, separators=(",", ":"))
    else:
        serialized_message_params = ""

    if serialized_message_params:
        interactive_msg.nativeFlowMessage.messageParamsJSON = serialized_message_params

    for btn_data in (buttons or []):
        if hasattr(btn_data, "serialized_params"):
            name = getattr(btn_data, "name", "")
            params_json = btn_data.serialized_params()
        elif isinstance(btn_data, dict):
            name = btn_data.get("name", btn_data.get("type", "quick_reply"))
            if "buttonParamsJSON" in btn_data and btn_data.get("buttonParamsJSON") is not None:
                params_json = btn_data["buttonParamsJSON"]
            elif "params" in btn_data and btn_data.get("params") is not None:
                params = btn_data["params"]
                if isinstance(params, str):
                    try:
                        json.loads(params)
                        params_json = params
                    except (ValueError, TypeError):
                        params_json = json.dumps({"value": params}, ensure_ascii=False)
                else:
                    params_json = json.dumps(params, ensure_ascii=False, separators=(",", ":"))
            else:
                params_json = "{}"
        else:
            name = getattr(btn_data, "name", "quick_reply")
            params_json = getattr(btn_data, "buttonParamsJSON", None) or "{}"

        btn = interactive_msg.nativeFlowMessage.buttons.add()
        btn.name = str(name or "quick_reply")
        btn.buttonParamsJSON = params_json or "{}"

    if not interactive_msg.header.title and not interactive_msg.header.hasMediaAttachment:
        if title:
            interactive_msg.header.title = title
        else:
            interactive_msg.header.title = "Action Required"

    interactive_msg.nativeFlowMessage.messageVersion = int(version or 1)

    msg = Message(
        interactiveMessage=interactive_msg,
        messageContextInfo=MessageContextInfo(
            deviceListMetadata=DeviceListMetadata(),
            deviceListMetadataVersion=2,
        ),
    )

    try:
        from neonize.exc import SendMessageError

        res = client.send_message(build_jid(jid), msg)
    except Exception as e:  # pragma: no cover - re-raised for controller
        error_str = str(e)
        logger.error(f"SendMessageError sending native flow: {error_str}")
        raise

    logger.info(f"Native flow message sent - ID: {getattr(res, 'ID', None)}")

    await _save_to_history(
        jid,
        {
            "interactiveMessage": {
                "body": {"text": text},
                "header": {"title": title} if title else {},
                "footer": {"text": footer} if footer else {},
                "nativeFlowMessage": {
                    "messageVersion": int(version or 1),
                    "messageParamsJSON": serialized_message_params or "",
                    "buttons": [
                        {"name": b.name, "buttonParamsJSON": b.buttonParamsJSON}
                        for b in interactive_msg.nativeFlowMessage.buttons
                    ],
                },
            },
            "messageContextInfo": {
                "deviceListMetadata": {},
                "deviceListMetadataVersion": 2,
            },
        },
        res,
        session_id,
    )
    await _dispatch_sent_event(jid, "native_flow", res, session_id)
    return res


# Backwards/alternate names.
send_native_flow = send_native_flow_message