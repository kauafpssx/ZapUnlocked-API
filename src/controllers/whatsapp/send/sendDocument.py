from src.utils.phone import resolve_jid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, File, Form, Request
from src.services.whatsapp.sender import send_document_message
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.utils.logger import logger
from src.utils.dry_run import is_dry_run, dry_run_media_response
import json
from src.utils.quote import build_send_options


@require_whatsapp
@handle_errors("send document")
async def send_document(
    request: Request,
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None),
    delay_message: Optional[str] = Form(None),
    delay_typing: Optional[float] = Form(None),
    mentioned: Optional[str] = Form(None),
):
    sid = get_session_id(request)
    logger.debug(f"🔍 POST /send_document: phone={phone}")

    path, size = await resolve_media(url, file, media_type="document")

    async def process_task():
        try:
            jid = resolve_jid(phone)
            options = await build_send_options(jid, reply_identifier=reply or quoted_id, delay_message=delay_message, delay_typing=delay_typing, mentioned=json.loads(mentioned) if mentioned else None)
            fn = file_name or (file.filename if file else None) or Path(path).name
            await send_document_message(jid, path, fn, "application/octet-stream", options=options, session_id=sid)
        finally:
            await upload_tracker.release(size)
            cleanup(path)

    if is_dry_run():
        return dry_run_media_response("Document sent successfully.")
    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Document sent successfully."}
