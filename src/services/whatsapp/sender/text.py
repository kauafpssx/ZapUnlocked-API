import asyncio

from src.services.whatsapp.sender.helpers import _ensure_client, _build_context_info, _save_to_history, build_jid, _dispatch_sent_event, apply_pre_send
from src.utils.errors import WhatsAppSendError
from src.utils.logger import logger


SEND_TIMEOUT_SECONDS = 15


async def _send_with_confirmation(client, target_jid, message):
    """Run Neonize's blocking send and require its server acknowledgement."""
    try:
        res = await asyncio.wait_for(
            asyncio.to_thread(client.send_message, target_jid, message),
            timeout=SEND_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise WhatsAppSendError(
            f"WhatsApp did not confirm the message within {SEND_TIMEOUT_SECONDS} seconds."
        ) from exc

    message_id = getattr(res, "ID", None) if res is not None else None
    if not message_id:
        logger.error(
            "WhatsApp send returned no message ID for target={} response_type={}",
            target_jid,
            type(res).__name__ if res is not None else "None",
        )
        raise WhatsAppSendError("WhatsApp did not acknowledge the message (missing message ID).")

    logger.info("WhatsApp accepted text message id={} target={}", message_id, target_jid)
    return res


async def send_message(jid: str, message: str, options: dict = None, session_id: str = "1"):
    client = _ensure_client(session_id)
    await apply_pre_send(jid, options, client)

    ci = _build_context_info(options.get("quoted"), options.get("mentioned") if options else None) if options else None

    if ci:
        from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message as WAMessage, ExtendedTextMessage
        msg_proto = WAMessage(
            extendedTextMessage=ExtendedTextMessage(
                text=message,
                contextInfo=ci
            )
        )
        res = await _send_with_confirmation(client, build_jid(jid), msg_proto)
    else:
        res = await _send_with_confirmation(client, build_jid(jid), message)

    await _save_to_history(jid, {"conversation": message}, res, session_id)
    await _dispatch_sent_event(jid, "text", res, session_id)
    return res
