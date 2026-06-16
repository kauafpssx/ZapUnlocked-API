from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.services.whatsapp import state
from src.services.whatsapp.messageFetcher import get_recent_chats as whatsapp_get_recent_chats
from src.utils.logger import logger


class RecentChatsRequest(BaseModel):
    limit: Optional[int] = 20


async def get_recent_chats(data: RecentChatsRequest, request: Request = None):
    sid = get_session_id(request)
    if not state.get_is_ready(sid):
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    limit = data.limit or 20

    try:
        chats = whatsapp_get_recent_chats(limit)
        return {
            "success": True,
            "requested": limit,
            "found": len(chats),
            "chats": chats,
        }
    except Exception as e:
        logger.error(f"❌ Failed to get recent chats: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
