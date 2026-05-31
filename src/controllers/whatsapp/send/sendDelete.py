from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import delete_message, find_message
from src.schemas import DeleteMessageRequest


@require_whatsapp
@handle_errors("delete message")
async def delete_msg(data: DeleteMessageRequest):
    """
    Delete a message by ID.
    fromMe=True deletes for everyone.
    fromMe=False deletes only on your side.
    """
    if not data.messageId:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'messageId' is required."})

    jid = f"{data.phone}@s.whatsapp.net"
    target_type = data.type or "id"
    target_id = data.messageId

    if target_type == "text":
        found_msg = await find_message(jid, data.messageId, target_type)
        if not found_msg:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Message not found by text."})
        target_id = found_msg["key"]["id"]

    await delete_message(jid, target_id, data.fromMe)
    return {"success": True, "message": "Message deleted."}
