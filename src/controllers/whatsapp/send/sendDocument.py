from pathlib import Path
from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_document_message
from src.services.media.downloader import download_media
from src.services.media.utils import cleanup
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendDocumentRequest

async def send_document(data: SendDocumentRequest):
    logger.info(f"🔍 Request recebida em /send_document para {data.phone}")

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

            file_path = await download_media(data.document_url)

            try:
                final_file_name = data.fileName or Path(file_path).name
                await send_document_message(jid, file_path, final_file_name, "application/octet-stream", options=options)
            finally:
                cleanup(file_path)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Documento enviado com sucesso ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar documento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
