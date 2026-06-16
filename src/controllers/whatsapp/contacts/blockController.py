from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from neonize.utils import build_jid
from neonize.utils.enum import BlocklistAction

from src.services.whatsapp import state
from src.schemas import BlockRequest
from src.utils.logger import logger


async def block_user(data: BlockRequest, request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.phone:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' is required."})

    if data.action not in ("block", "unblock"):
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": "'action' must be 'block' or 'unblock'."})

    action = BlocklistAction.BLOCK if data.action == "block" else BlocklistAction.UNBLOCK
    jid = build_jid(data.phone)

    try:
        sock.update_blocklist(jid, action)
    except Exception as e:
        logger.error(f"❌ Block/unblock failed for {data.phone}: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})

    return {
        "success": True,
        "phone": data.phone,
        "action": data.action,
        "message": f"User {data.phone} {'blocked' if data.action == 'block' else 'unblocked'} successfully.",
    }
