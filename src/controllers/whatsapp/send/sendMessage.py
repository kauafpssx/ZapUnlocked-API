from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_message as whatsapp_send_message
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.utils.formatter import format_text
from ..schemas import SendMessageRequest


async def send_message(data: SendMessageRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.phone or not data.message:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' and 'message' are required."})

    logger.debug(f"📥 POST /send: text={data.message!r}")

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        options = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        formatted_message = format_text(data.message)

        await whatsapp_send_message(jid, formatted_message, options)

        return {"success": True, "message": "Message sent."}
    except Exception as e:
        logger.error(f"❌ Erro ao enviar: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
