from src.utils.decorators import get_session_id
import asyncio
from fastapi import HTTPException, Request
from src.services.whatsapp.settingsService import get_settings, save_settings
from src.utils.logger import logger
from src.schemas import CallRejectRequest, CallRejectMessageRequest, AutoReadRequest


def _sid(request: Request) -> str:
    return get_session_id(request)


async def set_call_reject_auto(data: CallRejectRequest, request: Request):
    sid = _sid(request)
    try:
        save_settings({"call_reject_auto": data.value}, sid)
        logger.info(f"📞 Auto call reject: {data.value}")
        return {"success": True, "call_reject_auto": data.value}
    except Exception as e:
        logger.error(f"Failed to set call_reject_auto: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def set_call_reject_message(data: CallRejectMessageRequest, request: Request):
    sid = _sid(request)
    try:
        save_settings({"call_reject_message": data.value}, sid)
        logger.info("📞 Call reject message updated.")
        return {"success": True, "call_reject_message": data.value}
    except Exception as e:
        logger.error(f"Failed to set call_reject_message: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def set_auto_read_message(data: AutoReadRequest, request: Request):
    sid = _sid(request)
    try:
        save_settings({"auto_read_message": data.value}, sid)
        logger.info(f"✅ Auto-read messages: {data.value}")
        return {"success": True, "auto_read_message": data.value}
    except Exception as e:
        logger.error(f"Failed to set auto_read_message: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def get_phone_pair_code(phone: str, request: Request):
    sid = _sid(request)
    from src.services.whatsapp import state
    sock = state.get_client(sid)
    if not sock:
        raise HTTPException(
            status_code=503,
            detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected (client must be awaiting connection)."},
        )
    try:
        logger.info(f"📱 Generating pairing code for: {phone} (session={sid})")
        code = await asyncio.wait_for(
            asyncio.to_thread(sock.PairPhone, phone, True),
            timeout=15.0,
        )
        logger.info(f"✅ Code generated for {phone}: {code}")
        return {"success": True, "phone": phone, "code": code}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail={"error": "TIMEOUT", "message": "Timed out while generating pairing code."})
    except Exception as e:
        logger.error(f"Failed to generate pairing code: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
