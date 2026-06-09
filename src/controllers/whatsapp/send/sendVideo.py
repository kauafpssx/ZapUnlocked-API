from typing import Optional
from fastapi import UploadFile, File, Form
from src.services.whatsapp.sender import send_video_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.videoConverter import convert_to_mp4
from src.services.media.utils import cleanup, get_file_size
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.utils.logger import logger
from src.utils.dry_run import is_dry_run, dry_run_media_response
import json
from src.utils.quote import build_send_options


@require_whatsapp
@handle_errors("send video")
async def send_video(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    caption: str = Form(""),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    as_document: bool = Form(False),
    gif_playback: bool = Form(False),
    ptv: bool = Form(False),
    delay_message: Optional[str] = Form(None),
    delay_typing: Optional[float] = Form(None),
    mentioned: Optional[str] = Form(None),
):
    logger.debug(f"🔍 POST /send_video: phone={phone}")
    if is_dry_run():
        return dry_run_media_response("Video sent successfully.")
    path, size = await resolve_media(url, file, media_type="video")
    await _send_video_common(phone, path, size, caption, reply, quoted_id, as_document, gif_playback, ptv, delay_message, delay_typing, mentioned)
    return {"success": True, "message": "Video sent successfully."}


@require_whatsapp
@handle_errors("send gif")
async def send_gif(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    caption: str = Form(""),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    delay_message: Optional[str] = Form(None),
    delay_typing: Optional[float] = Form(None),
    mentioned: Optional[str] = Form(None),
):
    logger.debug(f"🔍 POST /send_gif: phone={phone}")
    if is_dry_run():
        return dry_run_media_response("GIF sent successfully.")
    path, size = await resolve_media(url, file, media_type="gif")
    await _send_video_common(phone, path, size, caption, reply, quoted_id, as_document=False, gif_playback=True, ptv=False, delay_message=delay_message, delay_typing=delay_typing, mentioned=mentioned)
    return {"success": True, "message": "GIF sent successfully."}


async def _send_video_common(phone, path, size, caption, reply, quoted_id, as_document, gif_playback, ptv, delay_message=None, delay_typing=None, mentioned=None):
    async def process_task():
        converted_path = None
        try:
            jid = f"{phone}@s.whatsapp.net"
            options = await build_send_options(jid, reply_identifier=reply or quoted_id, delay_message=delay_message, delay_typing=delay_typing, mentioned=json.loads(mentioned) if mentioned else None)

            final_path = path
            try:
                converted_path = await convert_to_mp4(path)
                final_path = converted_path
            except Exception:
                logger.error("⚠️ Video conversion failed, sending original...")

            file_size = get_file_size(final_path)
            should_be_doc = as_document or file_size > (15 * 1024 * 1024)
            final_ptv = False if should_be_doc else ptv
            final_gif = False if (should_be_doc or final_ptv) else gif_playback

            await send_video_message(jid, final_path, caption, as_document=should_be_doc, gif_playback=final_gif, ptv=final_ptv, options=options)
        finally:
            await upload_tracker.release(size)
            if converted_path:
                cleanup(converted_path)
            cleanup(path)

    from src.services.media.queue import task_queue
    await task_queue.enqueue(process_task())
