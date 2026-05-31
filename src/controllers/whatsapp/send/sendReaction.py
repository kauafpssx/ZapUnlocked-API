from fastapi import HTTPException
from src.services.whatsapp.sender import send_reaction as whatsapp_send_reaction
from src.utils.logger import logger
from src.utils.decorators import require_whatsapp, handle_errors
from src.schemas import SendReactionRequest

@require_whatsapp
@handle_errors("send reaction")
async def send_reaction(data: SendReactionRequest):
    identifier = data.reply or data.reaction or data.messageId or data.text
    identification_type = data.type or ("text" if (data.reply or data.text) and not data.messageId else "id")

    if not data.phone or not identifier or data.emoji is None:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone', a message identifier ('reaction'/'messageId'), and 'emoji' are required. Send an empty emoji to remove."})

    jid = f"{data.phone}@s.whatsapp.net"

    await whatsapp_send_reaction(jid, identifier, data.emoji, identification_type)
    return {"success": True, "message": "Reaction sent."}
