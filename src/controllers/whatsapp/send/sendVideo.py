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
    logger.debug(f"🔍 POST /send_video: phone={data.phone}")

    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

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
                    logger.error("⚠️ Video conversion failed, trying to send original...")

                file_size = get_file_size(final_path)
                should_be_doc = data.asDocument or file_size > (15 * 1024 * 1024)

                if should_be_doc:
                    mb_size = file_size / 1024 / 1024
                    logger.info(f"🎥 Large video detected ({mb_size:.2f}MB). Sending as document.")

                # Precedence logic:
                # 1. If document, PTV and GIF are disabled.
                # 2. PTV and GIF are mutually exclusive (PTV wins if both are true).
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
        return {"success": True, "message": "Video sent successfully."}

    except Exception as e:
        logger.error(f"❌ Failed to send video: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
