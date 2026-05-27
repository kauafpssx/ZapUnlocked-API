from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_reaction as whatsapp_send_reaction
from src.utils.logger import logger
from ..schemas import SendReactionRequest

async def send_reaction(data: SendReactionRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    identifier = data.reply or data.reaction or data.messageId or data.text
    identification_type = data.type or ("text" if (data.reply or data.text) and not data.messageId else "id")

    if not data.phone or not identifier or data.emoji is None:
        raise HTTPException(status_code=400, detail="phone, (reaction ou messageId) e emoji são obrigatórios (envie emoji vazio para remover)")

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        await whatsapp_send_reaction(jid, identifier, data.emoji, identification_type)
        return {"success": True, "message": "Reação enviada ✅"}
    except Exception as e:
        logger.error(f"❌ Erro ao enviar reação: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
