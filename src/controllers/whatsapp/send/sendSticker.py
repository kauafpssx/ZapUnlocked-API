from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_sticker_message
from src.services.media.downloader import download_media
from src.services.media.imageConverter import convert_to_webp
from src.services.media.utils import cleanup
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendStickerRequest

async def send_sticker(data: SendStickerRequest):
    logger.info(f"🔍 Request recebida em /send_sticker para {data.phone}")

    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"

            options = await resolve_quote(
                jid,
                reply_identifier=data.reply or data.quoted_id,
                reply_type=data.type or "id",
            )

            url = data.sticker_url or data.image_url
            if not url:
                raise Exception("sticker_url ou image_url é obrigatório")

            file_path = await download_media(url)
            sticker_path = None

            try:
                logger.info(f"🔄 Convertendo para sticker ({data.phone})...")
                sticker_path = await convert_to_webp(file_path, {
                    "resizeMode": data.resizeMode,
                    "padColor": data.padColor,
                    "blurIntensity": data.blurIntensity
                })
                logger.info(f"📤 Enviando sticker para {data.phone}...")
                await send_sticker_message(jid, sticker_path, data.pack or "", data.author or "", options=options)
            finally:
                cleanup(file_path)
                if sticker_path:
                    cleanup(sticker_path)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Figurinha enviada com sucesso ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar figurinha ({type(e).__name__}): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ({type(e).__name__}): {str(e)}")
