import asyncio

from src.schemas import BulkSendTextRequest
from src.services.whatsapp.sender import send_message as whatsapp_send_message
from src.services.whatsapp.sender.helpers import _parse_delay
from src.utils.decorators import require_whatsapp, handle_errors
from src.utils.formatter import format_text
from src.utils.quote import build_send_options
from src.utils.time import now_ts
from src.utils.logger import logger


@require_whatsapp
@handle_errors("bulk send")
async def send_bulk(data: BulkSendTextRequest):
    if not data.phones:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phones' cannot be empty."})

    formatted = format_text(data.message)
    results = []

    for i, phone in enumerate(data.phones):
        jid = f"{phone}@s.whatsapp.net"
        try:
            options = await build_send_options(
                jid,
                delay_message=data.delay_message,
                delay_typing=data.delay_typing,
                mentioned=data.mentioned,
            )
            res = await whatsapp_send_message(jid, formatted, options)
            msg_id = getattr(res, "ID", None) if res else None
            results.append({"phone": phone, "success": True, "messageId": msg_id, "timestamp": now_ts()})
            logger.debug(f"Bulk send [{i+1}/{len(data.phones)}] → {phone}")
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})
            logger.warning(f"Bulk send failed → {phone}: {e}")

        if i < len(data.phones) - 1 and data.delay_between is not None:
            secs = _parse_delay(data.delay_between)
            if secs > 0:
                await asyncio.sleep(secs)

    sent = sum(1 for r in results if r["success"])
    failed = len(results) - sent
    return {"success": True, "sent": sent, "failed": failed, "results": results}
