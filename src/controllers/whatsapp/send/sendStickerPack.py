from src.utils.phone import resolve_jid
from fastapi import HTTPException, Request
from src.utils.decorators import handle_errors, get_session_id
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.schemas.send import SendStickerPackRequest
from src.services.whatsapp.sender.sticker_pack import send_sticker_pack
import asyncio


@handle_errors("send sticker pack")
async def send_sticker_pack(data: SendStickerPackRequest, request: Request):
    sid = get_session_id(request)
    jid = resolve_jid(data.phone)
    if not data.files:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "files is required."})
    if is_dry_run():
        return dry_run_response("Sticker pack sent.")
    res = await send_sticker_pack(jid, data.files, data.packname or "Sticker pack", data.publisher or "", sid)
    return {"success": True, "message": "Sticker pack sent.", "count": len(res or [])}