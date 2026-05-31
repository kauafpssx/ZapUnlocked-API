from fastapi import HTTPException
from src.services.whatsapp.sender import send_message as whatsapp_send_message
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.utils.formatter import format_text
from src.utils.decorators import require_whatsapp, handle_errors
from src.schemas import SendMessageRequest


@require_whatsapp
@handle_errors("send message")
async def send_message(data: SendMessageRequest):
    if not data.phone or not data.message:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' and 'message' are required."})

    logger.debug(f"📥 POST /send: text={data.message!r}")

    jid = f"{data.phone}@s.whatsapp.net"

    options = await resolve_quote(
        jid,
        reply_identifier=data.reply or data.quoted_id,
        reply_type=data.type or "id",
    )

    formatted_message = format_text(data.message)

    await whatsapp_send_message(jid, formatted_message, options)

    return {"success": True, "message": "Message sent."}
