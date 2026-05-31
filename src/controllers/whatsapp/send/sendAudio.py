import time as time_module
from fastapi import HTTPException
from src.services.whatsapp.sender import send_audio_message, send_document_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.downloader import download_media
from src.services.media.audioConverter import convert_audio
from src.services.media.utils import cleanup, get_file_size
from src.services.media.queue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.schemas import SendAudioRequest

@require_whatsapp
@handle_errors("send audio")
async def send_audio(data: SendAudioRequest):
    logger.debug(f"🔍 POST /send_audio: phone={data.phone}")

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
                logger.info("🎵 Audio will be sent as a document.")
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
                    logger.error("⚠️ Mandatory conversion failed, trying to send original file...")

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
    return {"success": True, "message": "Audio sent successfully."}
