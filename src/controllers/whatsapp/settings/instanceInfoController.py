from fastapi import HTTPException
from src.services.whatsapp.client import get_client, get_is_ready
from src.utils.logger import logger
import asyncio


async def _get_client_info(info_type: str = "me") -> dict:
    """
    Fetch instance or device info via Neonize.
    info_type="me" returns profile data (phone, pushname, etc).
    info_type="device" returns device data (device, raw_agent, etc).
    """
    sock = get_client()
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        me = await asyncio.to_thread(sock.get_me)

        result = {"connected": get_is_ready()}

        if info_type == "device":
            # Device-specific fields
            result.update({
                "device": None,
                "raw_agent": None,
                "integrator": None,
            })
            try:
                result["device"] = me.JID.Device
                result["raw_agent"] = me.JID.RawAgent
                result["integrator"] = me.JID.Integrator
            except AttributeError:
                pass
            for field in ("Platform", "BusinessName"):
                try:
                    value = getattr(me, field, None)
                    if value is not None:
                        result[field.lower()] = str(value)
                except Exception:
                    pass
        else:
            # User/profile fields (default: "me")
            result.update({
                "phone": None,
                "jid": None,
                "server": None,
            })
            try:
                result["phone"] = me.JID.User
                result["jid"] = f"{me.JID.User}@{me.JID.Server}"
                result["server"] = me.JID.Server
            except AttributeError:
                pass
            for field in ("PushName", "BusinessName", "Platform", "AdvSecretKey"):
                try:
                    value = getattr(me, field, None)
                    if value:
                        result[field.lower()] = str(value)
                except Exception:
                    pass

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch instance data: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def get_instance_me():
    """Return instance profile data (phone, jid, PushName, etc)."""
    return await _get_client_info("me")


async def get_instance_device():
    """Return device data (Device, RawAgent, Integrator, etc)."""
    return await _get_client_info("device")
