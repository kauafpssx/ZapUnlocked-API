import time as time_module
from typing import Optional
from fastapi import UploadFile, File, Form
from src.services.whatsapp.sender import send_audio_message, send_document_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.audioConverter import convert_audio
from src.services.media.utils import cleanup, get_file_size
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.utils.logger import logger
from src.utils.dry_run import is_dry_run, dry_run_media_response
import json
from src.utils.quote import build_send_options


@require_whatsapp
@handle_errors("send audio")
async def send_audio(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    ptt: bool = Form(False),
    as_document: bool = Form(False),
    format: str = Form("m4a"),
    delay_message: Optional[str] = Form(None),
    delay_typing: Optional[float] = Form(None),
    mentioned: Optional[str] = Form(None),
):
    logger.debug(f"🔍 POST /send_audio: phone={phone}")

    path, size = await resolve_media(url, file, media_type="audio")

    async def process_task():
        try:
            jid = f"{phone}@s.whatsapp.net"
            options = await build_send_options(jid, reply_identifier=reply or quoted_id, delay_message=delay_message, delay_typing=delay_typing, mentioned=json.loads(mentioned) if mentioned else None)
            file_size = get_file_size(path)
            is_too_big = file_size > (15 * 1024 * 1024)

            if as_document or is_too_big:
                logger.info("🎵 Audio will be sent as a document.")
                filename = f"audio_{int(time_module.time() * 1000)}.mp3"
                await send_document_message(jid, path, filename, "audio/mpeg", options=options)
            else:
                converted_path = None
                duration = 0
                try:
                    converted_path, duration = await convert_audio(path, format)
                except Exception:
                    logger.error("⚠️ Audio conversion failed, sending original...")
                try:
                    await send_audio_message(jid, converted_path or path, is_ptt=ptt, duration=duration, options=options)
                finally:
                    if converted_path:
                        cleanup(converted_path)
        finally:
            await upload_tracker.release(size)
            cleanup(path)

    if is_dry_run():
        return dry_run_media_response("Audio sent successfully.")
    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Audio sent successfully."}
