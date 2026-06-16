from src.utils.decorators import get_session_id
from fastapi import HTTPException, Query, Request
from src.services.whatsapp import storage
from src.services.whatsapp.storage import get_recent_chats_from_index
from src.utils.phone import resolve_jid


async def list_chats(request: Request, limit: int = Query(default=20, ge=1, le=200)):
    sid = get_session_id(request)
    chats = get_recent_chats_from_index(sid)[:limit]
    return {"success": True, "total": len(chats), "chats": chats}


async def get_chat_messages(
    phone: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    sid = get_session_id(request)
    jid = resolve_jid(phone)
    phone_key = jid.split("@")[0]

    messages = await storage.get_history(phone_key, sid)
    if not messages:
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": f"No history found for {phone}."},
        )

    total = len(messages)
    sliced = list(reversed(messages))[offset: offset + limit]

    return {
        "success": True,
        "phone": phone,
        "total": total,
        "limit": limit,
        "offset": offset,
        "messages": sliced,
    }
