from src.utils.decorators import get_session_id
import asyncio
from fastapi import HTTPException, Request
from pydantic import BaseModel
from src.services.whatsapp import state
from src.utils.logger import logger
from ._db import resolve_jid, query_contact_db

class ContactRequest(BaseModel):
    phone: str

async def get_contact_info(data: ContactRequest, request: Request = None):
    sid = get_session_id(request)
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    phone = data.phone
    if not phone:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' is required."})

    jid = resolve_jid(phone)
    jid_str = f"{phone}@s.whatsapp.net"
    info = {
        "phone": phone,
        "jid": jid_str,
        "exists": False,
        "name": None,
        "fullName": None,
        "firstName": None,
        "pushName": None,
        "businessName": None,
        "profilePictureUrl": None,
        "status": None,
        "statusTimestamp": None,
        "businessProfile": None
    }

    logger.info(f"🔍 Fetching detailed info for {jid_str}")

    async def _run(fn, timeout, *args):
        try:
            return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout)
        except Exception:
            return None

    existence, pic_res = await asyncio.gather(
        _run(sock.is_on_whatsapp, 4.0, phone),
        _run(sock.get_profile_picture, 4.0, jid) if hasattr(sock, "get_profile_picture") else asyncio.sleep(0, None),
        return_exceptions=True,
    )

    if existence and len(existence) > 0:
        info["exists"] = existence[0].IsIn

    if pic_res and pic_res.URL:
        info["profilePictureUrl"] = pic_res.URL

    db = await asyncio.to_thread(query_contact_db, phone)
    if db:
        info["firstName"] = db.get("firstName")
        info["fullName"] = db.get("fullName")
        info["pushName"] = db.get("pushName")
        info["businessName"] = db.get("businessName")
        info["name"] = db.get("fullName") or db.get("pushName") or db.get("firstName") or db.get("businessName")

    if not info["status"] and hasattr(sock, "get_status_message"):
        status_data = await _run(sock.get_status_message, 3.0, jid)
        if status_data:
            info["status"] = status_data.Status
            info["statusTimestamp"] = int(status_data.Timestamp)

    if hasattr(sock, "get_business_profile"):
        business = await _run(sock.get_business_profile, 3.0, jid)
        if business:
            info["businessProfile"] = {
                "description": business.Description,
                "category": business.Category,
                "website": business.Website,
                "email": business.Email
            }

    logger.info(f"✅ Processing of {jid_str} complete.")
    return {"success": True, "data": info}
