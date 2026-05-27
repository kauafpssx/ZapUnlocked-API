from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_video_message
from src.services.media.downloader import download_media
from src.services.media.videoConverter import convert_to_mp4
from src.services.media.utils import cleanup, get_file_size
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendVideoRequest

async def send_video(data: SendVideoRequest):
    logger.info(f"🔍 Request recebida em /send_video para {data.phone}")

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

            file_path = await download_media(data.video_url)
            converted_path = None

            try:
                final_path = file_path
                try:
                    converted_path = await convert_to_mp4(file_path)
                    final_path = converted_path
                except Exception:
                    logger.error("⚠️ Falha na conversão de vídeo, tentando enviar original...")

                file_size = get_file_size(final_path)
                should_be_doc = data.asDocument or file_size > (15 * 1024 * 1024)

                if should_be_doc:
                    mb_size = file_size / 1024 / 1024
                    logger.info(f"🎥 Vídeo grande detectado ({mb_size:.2f}MB). Enviando como documento.")

                # Lógica de precedência solicitada pelo usuário:
                # 1. Se for documento, anula PTV e GIF.
                # 2. PTV e GIF são mutuamente exclusivos (PTV ganha se ambos vierem true).
                final_ptv = bool(data.ptv)
                final_gif = bool(data.gifPlayback)

                if should_be_doc:
                    final_ptv = False
                    final_gif = False
                elif final_ptv:
                    final_gif = False

                await send_video_message(
                    jid,
                    final_path,
                    data.caption or "",
                    as_document=should_be_doc,
                    gif_playback=final_gif,
                    ptv=final_ptv,
                    options=options
                )
            finally:
                if converted_path:
                    cleanup(converted_path)
                cleanup(file_path)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Vídeo enviado com sucesso ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar vídeo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
