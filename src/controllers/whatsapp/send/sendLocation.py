from src.utils.phone import resolve_jid
from fastapi import Request
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id
from src.services.whatsapp.sender import send_location_message
from src.services.media.queue import task_queue
from src.utils.quote import build_send_options
from src.schemas import SendLocationRequest


@require_whatsapp
@handle_errors("send location")
async def send_location(data: SendLocationRequest, request: Request):
    sid = get_session_id(request)

    async def process_task():
        jid = resolve_jid(data.phone)
        options = await build_send_options(jid, reply_identifier=data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
        await send_location_message(
            jid,
            latitude=data.lat,
            longitude=data.lng,
            name=data.name or "",
            address=data.address or "",
            options=options,
            session_id=sid,
        )

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Location sent."}
