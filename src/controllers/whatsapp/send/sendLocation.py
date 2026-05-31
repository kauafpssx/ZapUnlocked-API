from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import send_location_message
from src.services.media.queue import task_queue
from src.utils.quote import resolve_quote
from src.schemas import SendLocationRequest


@require_whatsapp
@handle_errors("send location")
async def send_location(data: SendLocationRequest):
    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"
        options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
        await send_location_message(
            jid,
            latitude=data.lat,
            longitude=data.lng,
            name=data.name or "",
            address=data.address or "",
            options=options,
        )

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Location sent."}
