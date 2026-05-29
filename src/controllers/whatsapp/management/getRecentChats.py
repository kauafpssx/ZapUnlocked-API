from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.messageFetcher import get_recent_chats as whatsapp_get_recent_chats
from src.utils.logger import logger

class RecentChatsRequest(BaseModel):
    limit: Optional[int] = 20

async def get_recent_chats(data: RecentChatsRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    limit = data.limit or 20

    try:
        chats = whatsapp_get_recent_chats(limit)

        return {
            "success": True,
            "requested": limit,
            "found": len(chats),
            "chats": chats
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter chats recentes: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
