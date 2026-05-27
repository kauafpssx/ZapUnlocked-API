import time as time_module
from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_audio_message, send_document_message
from src.services.media.downloader import download_media
from src.services.media.audioConverter import convert_audio
from src.services.media.utils import cleanup, get_file_size
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendAudioRequest

async def send_audio(data: SendAudioRequest):
    logger.info(f"🔍 Request recebida em /send_audio para {data.phone}")

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

            file_path = await download_media(data.audio_url)

            try:
                file_size = get_file_size(file_path)
                is_too_big = file_size > (15 * 1024 * 1024)

                if data.asDocument or is_too_big:
                    logger.info("🎵 Áudio será enviado como documento.")
                    filename = f"audio_{int(time_module.time() * 1000)}.mp3"
                    await send_document_message(jid, file_path, filename, "audio/mpeg", options=options)
                else:
                    final_path = file_path
                    converted_path = None
                    duration = 0
                    try:
                        converted_path, duration = await convert_audio(file_path, data.format or "m4a")
                        final_path = converted_path
                    except Exception:
                        logger.error("⚠️ Falha na conversão mandatória, tentando enviar arquivo original...")

                    try:
                        await send_audio_message(
                            jid, 
                            final_path, 
                            is_ptt=bool(data.ptt), 
                            duration=duration, 
                            options=options
                        )
                    finally:
                        if converted_path:
                            cleanup(converted_path)
            finally:
                if file_path:
                    cleanup(file_path)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Áudio enviado com sucesso ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar áudio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
