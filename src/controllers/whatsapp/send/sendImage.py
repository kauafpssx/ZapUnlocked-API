from typing import Optional
from fastapi import UploadFile, File, Form
from src.services.whatsapp.sender import send_image_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.utils.logger import logger
from src.utils.quote import resolve_quote


@require_whatsapp
@handle_errors("send image")
async def send_image(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    caption: str = Form(""),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    as_document: bool = Form(False),
    file_name: Optional[str] = Form(None),
):
    logger.debug(f"🔍 POST /send_image: phone={phone}")

    path, size = await resolve_media(url, file, media_type="image")

    async def process_task():
        try:
            jid = f"{phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=reply or quoted_id)
            fn = file_name or (file.filename if file else None)
            await send_image_message(jid, path, caption=caption, as_document=as_document, file_name=fn, options=options)
        finally:
            await upload_tracker.release(size)
            cleanup(path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Image sent successfully."}
