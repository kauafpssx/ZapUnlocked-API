from src.utils.phone import resolve_jid
from fastapi import HTTPException, Request
from src.services.whatsapp.sender.helpers import _ensure_client, build_jid
from src.utils.decorators import handle_errors, get_session_id
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.schemas.send import SendAlbumRequest
import asyncio


@handle_errors("send album")
async def send_album(data: SendAlbumRequest, request: Request):
    sid = get_session_id(request)
    jid = resolve_jid(data.phone)
    client = _ensure_client(sid)
    if not data.files:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "files is required."})
    if is_dry_run():
        return dry_run_response("Album sent.")
    res = await asyncio.to_thread(client.send_album, build_jid(jid), data.files, data.caption or "", None, bool(data.spoiler))
    return {"success": True, "message": "Album sent.", "results": [getattr(r, "ID", None) for r in (res or [])]}