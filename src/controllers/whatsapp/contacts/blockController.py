from fastapi import HTTPException
from neonize.utils import build_jid
from neonize.utils.enum import BlocklistAction

from src.services.whatsapp.client import get_sock
from src.controllers.whatsapp.schemas import BlockRequest


async def block_user(data: BlockRequest):
    sock = get_sock()
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.phone:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' is required."})

    if data.action not in ("block", "unblock"):
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": "'action' must be 'block' or 'unblock'."})

    jid = build_jid(data.phone)
    action = BlocklistAction.BLOCK if data.action == "block" else BlocklistAction.UNBLOCK

    try:
        sock.update_blocklist(jid, action)
        return {
            "success": True,
            "phone": data.phone,
            "action": data.action,
            "message": f"User {data.phone} {'blocked' if data.action == 'block' else 'unblocked'} successfully.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
