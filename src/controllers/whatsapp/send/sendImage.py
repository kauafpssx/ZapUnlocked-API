from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_image_message
from src.services.media.downloader import download_media
from src.services.media.utils import cleanup
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendMediaRequest

async def send_image(data: SendMediaRequest):
    logger.info(f"🔍 Request recebida em /send_image para {data.phone}")

    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.phone or not data.image_url:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' and 'image_url' are required."})

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"

            options = await resolve_quote(
                jid,
                reply_identifier=data.reply or data.quoted_id,
                reply_type=data.type or "id",
            )

            logger.info(f"📥 Baixando imagem para {data.phone}...")
            file_path = await download_media(data.image_url)

            try:
                final_as_document = bool(data.asDocument)
                final_file_name = data.fileName or None
                logger.info(f"📤 Enviando imagem para {data.phone}{' como documento' if final_as_document else ''}...")
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

    except Exception as e:
        logger.error(f"❌ Erro ao enviar imagem: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
