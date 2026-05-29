import asyncio
from fastapi import HTTPException
from pydantic import BaseModel
from src.services.whatsapp.client import get_sock
import asyncio
from fastapi import HTTPException
from pydantic import BaseModel
from src.services.whatsapp.client import get_sock
from src.utils.logger import logger
from neonize.utils import build_jid

class ContactRequest(BaseModel):
    phone: str

async def get_contact_info(data: ContactRequest):
    sock = get_sock()
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    phone = data.phone
    if not phone:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'phone' is required."})

    jid_str = f"{phone}@s.whatsapp.net"
    jid = build_jid(jid_str)
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

    # 1. Check if number exists on WhatsApp
    try:
        logger.debug(f"👀 Checking existence of {phone}...")
        # Corrigido: a resposta do is_on_whatsapp usa o campo 'IsIn'
        results = await asyncio.wait_for(asyncio.to_thread(sock.is_on_whatsapp, phone), timeout=4.0)
        if results and len(results) > 0:
            info["exists"] = results[0].IsIn
            logger.debug(f"✅ Existence: {info['exists']}")
        else:
            info["exists"] = False
    except Exception as e:
        logger.debug(f"⚠️ Existence check failed: {e}")
        info["exists"] = "unknown"

    # 2. Contact info (names) via ContactStore
    try:
        if hasattr(sock, "contact"):
            logger.debug("👤 Fetching contact data via ContactStore...")
            contact = await asyncio.wait_for(asyncio.to_thread(sock.contact.get_contact, jid), timeout=3.0)
            if contact:
                info["fullName"] = contact.FullName or None
                info["firstName"] = contact.FirstName or None
                info["pushName"] = contact.PushName or None
                info["businessName"] = contact.BusinessName or None
                # Prioridade: Full > Push > First > Business
                info["name"] = info["fullName"] or info["pushName"] or info["firstName"] or info["businessName"]
                logger.debug(f"✅ Dados da Store obtidos. Nome: {info['name']}")
    except Exception as e:
        logger.debug(f"⚠️ ContactStore fetch failed: {e}")

    # 3. User info (status and name fallback)
    try:
        logger.debug("👤 Fetching data via get_user_info...")
        user_infos = await asyncio.wait_for(asyncio.to_thread(sock.get_user_info, jid), timeout=4.0)
        if user_infos and len(user_infos) > 0:
            u_info = user_infos[0].UserInfo
            if u_info.Status:
                info["status"] = u_info.Status

            # Fallback para nome se estiver vazio
            if not info["name"] and u_info.VerifiedName:
                info["name"] = u_info.VerifiedName.Details.VerifiedName or u_info.VerifiedName.Details.PublicName

            logger.debug(f"✅ User data fetched. Status: {info['status']}")
    except Exception as e:
        logger.debug(f"⚠️ get_user_info fetch failed: {e}")

    # 4. Foto de Perfil
    try:
        logger.debug(f"📸 Obtendo foto de perfil...")
        res = await asyncio.wait_for(asyncio.to_thread(sock.get_profile_picture, jid), timeout=4.0)
        if res and res.URL:
            info["profilePictureUrl"] = res.URL
            logger.debug("✅ Foto de perfil obtida.")
    except Exception:
        pass

    # 5. Status Fallback
    if not info["status"]:
        try:
            if hasattr(sock, "get_status_message"):
                status_data = await asyncio.wait_for(asyncio.to_thread(sock.get_status_message, jid), timeout=3.0)
                if status_data:
                    info["status"] = status_data.Status
                    info["statusTimestamp"] = int(status_data.Timestamp)
        except Exception:
            pass

    # 6. Perfil Comercial
    try:
        if hasattr(sock, "get_business_profile"):
            business = await asyncio.wait_for(asyncio.to_thread(sock.get_business_profile, jid), timeout=3.0)
            if business:
                info["businessProfile"] = {
                    "description": business.Description,
                    "category": business.Category,
                    "website": business.Website,
                    "email": business.Email
                }
    except Exception:
        pass

    logger.info(f"✅ Processing of {jid_str} complete.")
    return {"success": True, "data": info}
