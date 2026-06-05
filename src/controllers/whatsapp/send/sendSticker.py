from typing import Optional
from fastapi import UploadFile, File, Form
from src.services.whatsapp.sender import send_sticker_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.imageConverter import convert_to_webp, convert_to_animated_webp
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.services.media.resolver import resolve_media
from src.services.media import upload_tracker
from src.services.media.validator import is_animated_sticker_source
from src.utils.logger import logger
from src.utils.quote import resolve_quote


@require_whatsapp
@handle_errors("send sticker")
async def send_sticker(
    phone: str = Form(...),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    reply: Optional[str] = Form(None),
    quoted_id: Optional[str] = Form(None),
    pack: Optional[str] = Form(""),
    author: Optional[str] = Form(""),
    resize_mode: str = Form("pad"),
    pad_color: str = Form("black"),
    blur_intensity: int = Form(20),
):
    logger.debug(f"🔍 POST /send_sticker: phone={phone}")

    path, size = await resolve_media(url, file, media_type="sticker")

    async def process_task():
        sticker_path = None
        try:
            jid = f"{phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=reply or quoted_id)

            conv_options = {"resizeMode": resize_mode, "padColor": pad_color, "blurIntensity": blur_intensity}

            from src.services.media.validator import _detect, _normalize
            mime = _normalize(_detect(path))

            logger.info(f"🔄 Converting to sticker ({phone}), mime={mime}...")
            animated = is_animated_sticker_source(mime)
            if animated:
                sticker_path = await convert_to_animated_webp(path, conv_options)
            else:
                sticker_path = await convert_to_webp(path, conv_options)

            logger.info(f"📤 Sending sticker to {phone} (animated={animated})...")
            await send_sticker_message(jid, sticker_path, pack or "", author or "", options=options, passthrough=animated)
        finally:
            await upload_tracker.release(size)
            cleanup(path)
            if sticker_path:
                cleanup(sticker_path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Sticker sent successfully."}
