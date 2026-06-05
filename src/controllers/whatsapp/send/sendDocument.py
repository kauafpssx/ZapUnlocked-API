from pathlib import Path
from typing import Optional
from fastapi import UploadFile, File, Form
from src.services.whatsapp.sender import send_document_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.utils.logger import logger
from src.utils.quote import resolve_quote


@require_whatsapp
@handle_errors("send document")
async def send_document(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None),
):
    logger.debug(f"🔍 POST /send_document: phone={phone}")

    path, size = await resolve_media(url, file, media_type="document")

    async def process_task():
        try:
            jid = f"{phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=reply or quoted_id)
            fn = file_name or (file.filename if file else None) or Path(path).name
            await send_document_message(jid, path, fn, "application/octet-stream", options=options)
        finally:
            await upload_tracker.release(size)
            cleanup(path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Document sent successfully."}
