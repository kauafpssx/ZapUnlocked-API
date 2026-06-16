from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from src.services.whatsapp import state
from src.services.whatsapp.messageFetcher import fetch_messages as whatsapp_fetch_messages
from src.services.webhooks.service import trigger_webhook
from src.utils.logger import logger

class FetchMessagesRequest(BaseModel):
    phone: str
    limit: Optional[int] = 20
    type: Optional[str] = "all"
    webhook: Optional[dict] = None
    onlyReactions: Optional[bool] = None
    reactionEmoji: Optional[str] = None
    query: Optional[str] = None
    onlyButtons: Optional[bool] = None

async def fetch_messages(data: FetchMessagesRequest, request: Request = None):
    sid = get_session_id(request)
    if not state.get_is_ready(sid):
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.phone:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' is required."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        filters = {
            "onlyReactions": data.onlyReactions,
            "reactionEmoji": data.reactionEmoji,
            "query": data.query,
            "onlyButtons": data.onlyButtons
        }

        result = await whatsapp_fetch_messages(jid, data.limit or 20, data.type or "all", filters)

        if data.webhook and data.webhook.get("url"):
            import asyncio
            asyncio.create_task(trigger_webhook(data.webhook, {
                "phone": data.phone,
                "requested": str(result.get("requested", 0)),
                "found": str(result.get("found", 0)),
                "text": f"Retrieved history of {result.get('found', 0)} messages."
            }))

        return {
            "success": True,
            "phone": data.phone,
            **result
        }
    except Exception as e:
        logger.error(f"❌ Failed to fetch messages for {data.phone}: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
