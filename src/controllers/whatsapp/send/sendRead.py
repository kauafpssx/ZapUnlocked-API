from src.utils.phone import resolve_jid
from fastapi import HTTPException, Request
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id
from src.services.whatsapp.sender import mark_messages_read, find_message
from src.schemas import ReadMessagesRequest


@require_whatsapp
@handle_errors("read messages")
async def read_messages(data: ReadMessagesRequest, request: Request):
    sid = get_session_id(request)
    if not data.messageIds:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'messageIds' cannot be empty."})

    jid = resolve_jid(data.phone)
    target_type = data.type or "id"

    target_ids = []
    for msg_identifier in data.messageIds:
        if target_type == "text":
            found_msg = await find_message(jid, msg_identifier, target_type, session_id=sid)
            if found_msg:
                target_ids.append(found_msg["key"]["id"])
        else:
            target_ids.append(msg_identifier)

    if not target_ids:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "No messages found to mark as read."})

    await mark_messages_read(jid, target_ids, data.sender, session_id=sid)
    return {"success": True, "message": f"{len(target_ids)} message(s) marked as read."}
