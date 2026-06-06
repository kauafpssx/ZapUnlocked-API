from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import send_contacts_message
from src.services.media.queue import task_queue
from src.utils.quote import build_send_options
from src.schemas import SendContactsRequest


@require_whatsapp
@handle_errors("send contacts")
async def send_contacts(data: SendContactsRequest):
    if not data.contacts:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "At least one contact is required."})

    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"
        options = await build_send_options(jid, reply_identifier=data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
        contacts_list = [{"name": c.name, "phone": c.phone} for c in data.contacts]
        await send_contacts_message(jid, contacts_list, options=options)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": f"{len(data.contacts)} contact(s) sent."}
