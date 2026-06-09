import asyncio
from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.utils.phone import resolve_jid
from src.utils.logger import logger


@require_whatsapp
@handle_errors("get contact")
async def get_contact(phone: str):
    from src.services.whatsapp.client import get_client
    from src.services.whatsapp.sender.helpers import build_jid

    client = get_client()
    jid_obj = build_jid(resolve_jid(phone))

    name = None
    status = None
    picture_url = None

    # Contact info (name from device contacts / WhatsApp)
    try:
        info = await asyncio.to_thread(client.get_contact, jid_obj)
        name = getattr(info, "FullName", None) or getattr(info, "PushName", None) or getattr(info, "BusinessName", None)
    except Exception as e:
        logger.debug(f"[contacts] get_contact failed for {phone}: {e}")

    # User info (status text, verified name)
    try:
        users = await asyncio.to_thread(client.get_user_info, [jid_obj])
        if users:
            u = users[0]
            status = getattr(u, "Status", None) or None
            if not name:
                name = getattr(u, "VerifiedName", None) or None
    except Exception as e:
        logger.debug(f"[contacts] get_user_info failed for {phone}: {e}")

    # Profile picture URL
    try:
        pic = await asyncio.to_thread(client.get_profile_picture, jid_obj)
        picture_url = getattr(pic, "URL", None) or None
    except Exception as e:
        logger.debug(f"[contacts] get_profile_picture failed for {phone}: {e}")

    return {
        "success": True,
        "phone": phone,
        "jid": resolve_jid(phone),
        "name": name,
        "status": status,
        "profilePictureUrl": picture_url,
    }
