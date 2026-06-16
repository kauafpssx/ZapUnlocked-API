from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from src.services.whatsapp import state
from src.utils.logger import logger
import asyncio


async def _get_client_info(info_type: str = "me", session_id: str = "1") -> dict:
    sock = state.get_client(session_id)
    if not sock:
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        me = await asyncio.to_thread(sock.get_me)

        result = {"connected": state.get_is_ready(session_id)}

        if info_type == "device":
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


async def get_instance_me(request: Request = None):
    sid = get_session_id(request)
    return await _get_client_info("me", sid)


async def get_instance_device(request: Request = None):
    sid = get_session_id(request)
    return await _get_client_info("device", sid)
