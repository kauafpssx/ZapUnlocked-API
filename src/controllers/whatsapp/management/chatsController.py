from fastapi import HTTPException, Query
from src.services.whatsapp import storage
from src.services.whatsapp.messageFetcher import get_recent_chats as _recent_chats
from src.utils.phone import resolve_jid


async def list_chats(limit: int = Query(default=20, ge=1, le=200)):
    chats = _recent_chats(limit)
    return {"success": True, "total": len(chats), "chats": chats}


async def get_chat_messages(
    phone: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    jid = resolve_jid(phone)
    phone_key = jid.split("@")[0]

    messages = await storage.get_history(phone_key)
    if not messages:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": f"No history found for {phone}."},
        )

    total = len(messages)
    # newest first
    sliced = list(reversed(messages))[offset: offset + limit]

    return {
        "success": True,
        "phone": phone,
        "total": total,
        "limit": limit,
        "offset": offset,
        "messages": sliced,
    }
