from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import send_contact_message
from src.services.media.queue import task_queue
from src.utils.quote import build_send_options
from src.schemas import SendContactRequest


@require_whatsapp
@handle_errors("send contact")
async def send_contact(data: SendContactRequest):
    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"
        options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
        await send_contact_message(
            jid,
            contact_name=data.name,
            contact_phone=data.contactPhone,
            options=options,
        )

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Contact sent."}
