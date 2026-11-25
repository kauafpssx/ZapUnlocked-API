from fastapi import Request
from src.utils.decorators import get_session_id
from src.repositories import message_status as ms_repo


async def get_message_status(request: Request, message_id: str):
    sid = get_session_id(request)
    row = ms_repo.get_status(sid, message_id)
    if not row:
        return {"success": False, "message": "Status not found.", "messageId": message_id}
    return {
        "success": True,
        "messageId": message_id,
        "status": row.get("status"),
        "chatJid": row.get("chat_jid"),
        "receiptType": row.get("receipt_type"),
        "timestamp": row.get("timestamp"),
        "updatedAt": row.get("updated_at"),
    }