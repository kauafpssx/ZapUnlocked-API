from pathlib import Path
from fastapi import HTTPException
from src.services.whatsapp.sender import send_document_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.services.media.downloader import download_media
from src.services.media.utils import cleanup
from src.services.media.queue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from src.schemas import SendDocumentRequest

@require_whatsapp
@handle_errors("send document")
async def send_document(data: SendDocumentRequest):
    logger.debug(f"🔍 POST /send_document: phone={data.phone}")

    async def process_task():
        jid = f"{data.phone}@s.whatsapp.net"

        options = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        file_path = await download_media(data.document_url)

        try:
            final_file_name = data.fileName or Path(file_path).name
            await send_document_message(jid, file_path, final_file_name, "application/octet-stream", options=options)
        finally:
            cleanup(file_path)

    await task_queue.enqueue(process_task())
    return {"success": True, "message": "Document sent successfully."}
