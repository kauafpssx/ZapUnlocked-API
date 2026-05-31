from src.services.whatsapp.sender.helpers import _ensure_client, _build_context_info, _save_to_history, build_jid, _dispatch_sent_event
from src.services.whatsapp import settingsService


async def send_message(jid: str, message: str, options: dict = None):
    client = _ensure_client()

    # Appending AI Tag if enabled
    settings = settingsService.get_settings()

    if settings.get("ai_tag_enabled"):
        tag = settings.get("ai_tag_text", " (ZapUnlocked AI)")
        if tag not in message:
            message += tag

    ci = _build_context_info(options.get("quoted")) if options else None

    if ci:
        from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message as WAMessage, ExtendedTextMessage
        msg_proto = WAMessage(
            extendedTextMessage=ExtendedTextMessage(
                text=message,
                contextInfo=ci
            )
        )
        res = client.send_message(build_jid(jid), msg_proto)
    else:
        res = client.send_message(build_jid(jid), message)

    await _save_to_history(jid, {"conversation": message}, res)
    await _dispatch_sent_event(jid, "text", res)
    return res
