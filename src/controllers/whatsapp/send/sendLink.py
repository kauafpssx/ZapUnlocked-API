from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.whatsapp.sender import send_link_message
from src.services.media.queue import task_queue
from src.utils.quote import build_send_options
from src.schemas import SendLinkRequest


@require_whatsapp
@handle_errors("send link")
async def send_link(data: SendLinkRequest):
    if not data.url:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'url' is required."})

    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"
        options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
        await send_link_message(
            jid,
            url=str(data.url),
            text=data.text or "",
            title=data.title or "",
            description=data.description or "",
            thumbnail_url=data.thumbnailUrl,
            options=options,
        )

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Link sent."}
