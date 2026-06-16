from src.utils.phone import resolve_jid
from fastapi import HTTPException, Request
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id
from src.services.whatsapp.sender import delete_message, find_message
from src.schemas import DeleteMessageRequest


@require_whatsapp
@handle_errors("delete message")
async def delete_msg(data: DeleteMessageRequest, request: Request):
    sid = get_session_id(request)
    if not data.messageId:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'messageId' is required."})

    jid = resolve_jid(data.phone)
    target_type = data.type or "id"
    target_id = data.messageId

    if target_type == "text":
        found_msg = await find_message(jid, data.messageId, target_type, session_id=sid)
        if not found_msg:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Message not found by text."})
        target_id = found_msg["key"]["id"]

    await delete_message(jid, target_id, data.fromMe, session_id=sid)
    return {"success": True, "message": "Message deleted."}
