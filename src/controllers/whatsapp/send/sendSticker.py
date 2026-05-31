from fastapi import HTTPException
from src.services.whatsapp.sender import send_sticker_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.downloader import download_media
from src.services.media.imageConverter import convert_to_webp
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.schemas import SendStickerRequest

@require_whatsapp
@handle_errors("send sticker")
async def send_sticker(data: SendStickerRequest):
    logger.debug(f"🔍 POST /send_sticker: phone={data.phone}")

    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"

        options = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        url = data.sticker_url or data.image_url
        if not url:
            raise Exception("'sticker_url' or 'image_url' is required.")

        file_path = await download_media(url)
        sticker_path = None

        try:
            logger.info(f"🔄 Converting to sticker ({data.phone})...")
            sticker_path = await convert_to_webp(file_path, {
                "resizeMode": data.resizeMode,
                "padColor": data.padColor,
                "blurIntensity": data.blurIntensity
            })
            logger.info(f"📤 Sending sticker to {data.phone}...")
            await send_sticker_message(jid, sticker_path, data.pack or "", data.author or "", options=options)
        finally:
            cleanup(file_path)
            if sticker_path:
                cleanup(sticker_path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Sticker sent successfully."}
