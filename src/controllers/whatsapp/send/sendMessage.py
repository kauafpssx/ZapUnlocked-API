from src.utils.phone import resolve_jid
from fastapi import HTTPException
from src.services.whatsapp.sender import send_message as whatsapp_send_message
from src.utils.logger import logger
from src.utils.quote import build_send_options
from src.utils.formatter import format_text
from src.utils.decorators import require_whatsapp, handle_errors
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.schemas import SendMessageRequest


@require_whatsapp
@handle_errors("send message")
async def send_message(data: SendMessageRequest):
    if not data.phone or not data.message:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' and 'message' are required."})

    logger.debug(f"📥 POST /send: text={data.message!r}")

    jid = resolve_jid(data.phone)

    if is_dry_run():
        return dry_run_response("Message sent.")

    options = await build_send_options(
        jid,
        reply_identifier=data.quoted_id,
        reply_type=data.type or "id",
        delay_message=data.delay_message,
        delay_typing=data.delay_typing,
        mentioned=data.mentioned,
    )

    formatted_message = format_text(data.message)
    res = await whatsapp_send_message(jid, formatted_message, options)
    return sent_response(res, "Message sent.")
