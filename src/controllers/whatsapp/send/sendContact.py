from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import send_contact_message
from src.services.media.queue import task_queue
from src.utils.quote import resolve_quote
from src.schemas import SendContactRequest


@require_whatsapp
@handle_errors("send contact")
async def send_contact(data: SendContactRequest):
    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"
        options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
        await send_contact_message(
            jid,
            contact_name=data.name,
            contact_phone=data.contactPhone,
            options=options,
        )

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Contact sent."}
