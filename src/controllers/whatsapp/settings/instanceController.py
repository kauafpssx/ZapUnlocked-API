import asyncio
from fastapi import HTTPException
from src.services.whatsapp.client import get_client
from src.services.whatsapp.settingsService import get_settings, save_settings
from src.utils.logger import logger
from src.schemas import CallRejectRequest, CallRejectMessageRequest, AutoReadRequest


# ─────────────────────────────────────────────
# Calls — Auto-reject
# ─────────────────────────────────────────────

async def set_call_reject_auto(data: CallRejectRequest):
    """
    Enable or disable automatic call rejection.
    Stored locally in settings.json — the event handler
    uses this setting to decide whether to auto-reject incoming calls.
    """
    try:
        save_settings({"call_reject_auto": data.value})
        logger.info(f"📞 Auto call reject: {data.value}")
        return {"success": True, "call_reject_auto": data.value}
    except Exception as e:
        logger.error(f"Failed to set call_reject_auto: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def set_call_reject_message(data: CallRejectMessageRequest):
    """
    Sets the message sent automatically when a call is rejected.
    Stored locally in settings.json.
    """
    try:
        save_settings({"call_reject_message": data.value})
        logger.info("📞 Call reject message updated.")
        return {"success": True, "call_reject_message": data.value}
    except Exception as e:
        logger.error(f"Failed to set call_reject_message: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ─────────────────────────────────────────────
# Auto-read messages
# ─────────────────────────────────────────────

async def set_auto_read_message(data: AutoReadRequest):
    """
    Enable or disable automatic message read receipts.
    Stored locally in settings.json — the messageHandler
    uses this setting to mark messages as read upon receipt.
    """
    try:
        save_settings({"auto_read_message": data.value})
        logger.info(f"✅ Auto-read messages: {data.value}")
        return {"success": True, "auto_read_message": data.value}
    except Exception as e:
        logger.error(f"Failed to set auto_read_message: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ─────────────────────────────────────────────
# Connect via phone pairing code
# ─────────────────────────────────────────────

async def get_phone_pair_code(phone: str):
    """
    Generate a pairing code to connect a number without QR Code.
    Enter the code directly in WhatsApp (Linked Devices > Link with phone number).

    Requires client to be awaiting connection (no active session).
    """
    sock = get_client()
    if not sock:
        raise HTTPException(
            status_code=503,
            detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected (client must be awaiting connection)."},
        )

    try:
        logger.info(f"📱 Generating pairing code for: {phone}")
        # PairPhone is synchronous; requires client in awaiting-connection mode
        # Returns the 8-digit code as a string
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
