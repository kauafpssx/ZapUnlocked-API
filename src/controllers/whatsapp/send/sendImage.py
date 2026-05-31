from fastapi import HTTPException
from src.services.whatsapp.sender import send_image_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.downloader import download_media
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.schemas import SendMediaRequest

@require_whatsapp
@handle_errors("send image")
async def send_image(data: SendMediaRequest):
    logger.debug(f"🔍 POST /send_image: phone={data.phone}")

    if not data.phone or not data.image_url:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' and 'image_url' are required."})

    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"

        options = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        logger.debug(f"📥 Downloading image for {data.phone}...")
        file_path = await download_media(data.image_url)

        try:
            final_as_document = bool(data.asDocument)
            final_file_name = data.fileName or None
            logger.debug(f"📤 Sending image to {data.phone}{' as document' if final_as_document else ''}...")
            await send_image_message(
                jid, file_path,
                caption=data.caption or "",
                as_document=final_as_document,
                file_name=final_file_name,
                options=options
            )
        finally:
            if file_path:
                cleanup(file_path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Image sent successfully."}
