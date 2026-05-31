from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import edit_message, find_message
from src.schemas import SendEditMessageRequest


@require_whatsapp
@handle_errors("edit message")
async def send_edit(data: SendEditMessageRequest):
    """Edit a previously sent message."""
    jid = f"{data.phone}@s.whatsapp.net"
    target_type = data.type or "id"
    target_id = data.messageId

    if target_type == "text":
        found_msg = await find_message(jid, data.messageId, target_type)
        if not found_msg:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Message not found to edit."})
        target_id = found_msg["key"]["id"]

    await edit_message(jid, target_id, data.message)
    return {"success": True, "message": "Message edited."}
