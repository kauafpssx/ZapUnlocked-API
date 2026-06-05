import asyncio
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException
from neonize.utils.enum import PrivacySettingType, PrivacySetting
from src.services.whatsapp.client import get_client
from src.utils.logger import logger


_FIELD_TO_TYPE = {
    "lastSeen": PrivacySettingType.LAST_SEEN,
    "online": PrivacySettingType.ONLINE,
    "profile": PrivacySettingType.PROFILE,
    "status": PrivacySettingType.STATUS,
    "readReceipts": PrivacySettingType.READ_RECEIPTS,
    "groupsAdd": PrivacySettingType.GROUP_ADD,
    "callAdd": PrivacySettingType.CALL_ADD,
}


class PrivacyValueRequest(BaseModel):
    value: Optional[str] = None


class AboutRequest(BaseModel):
    value: Optional[str] = None


class DisappearingTimerRequest(BaseModel):
    value: Optional[int] = None


_SETTING_INT_TO_STR = {
    1: "undefined",
    2: "all",
    3: "contacts",
    4: "contacts_blacklist",
    5: "match_last_seen",
    6: "known",
    7: "none",
}

_FIELD_TO_PROTO_ATTR = {
    "lastSeen": "LastSeen",
    "online": "Online",
    "profile": "Profile",
    "status": "Status",
    "readReceipts": "ReadReceipts",
    "groupsAdd": "GroupAdd",
    "callAdd": "CallAdd",
}


async def _get_current_privacy(field: str) -> dict:
    sock = _require_client()
    settings = await asyncio.to_thread(sock.get_privacy_settings)
    attr = _FIELD_TO_PROTO_ATTR.get(field)
    int_val = getattr(settings, attr, 0) if attr else 0
    return {"success": True, "field": field, "value": _SETTING_INT_TO_STR.get(int_val, "unknown")}


def _require_client():
    sock = get_client()
    if not sock:
        raise HTTPException(
            status_code=503,
            detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."},
        )
    return sock


def _set_privacy_direct(sock, pstype: PrivacySettingType, psvalue: PrivacySetting):
    """
    Neonize bug workaround: client.py calls .decode() on POINTER(Bytes) return
    which causes LP_Bytes error. Call Go directly, check for NULL (success),
    then deserialize error proto only if pointer is non-null.
    """
    from neonize._binder import free_bytes
    from neonize.proto.Neonize_pb2 import ReturnFunctionWithError

    bytes_ptr = sock._NewClient__client.SetPrivacySetting(
        sock.uuid,
        pstype.value.encode(),
        psvalue.value.encode(),
    )
    if not bytes_ptr:
        return
    protobytes = bytes_ptr.contents.get_bytes()
    free_bytes(bytes_ptr)
    if not protobytes:
        return
    logger.debug(f"SetPrivacySetting raw response ({len(protobytes)}b): {protobytes.hex()}")
    result = ReturnFunctionWithError.FromString(protobytes)
    if result.Error:
        # Only raise if error looks like a readable string, not binary proto data
        is_binary = any(b < 0x20 and b not in (0x09, 0x0A, 0x0D) for b in result.Error.encode("utf-8", errors="replace"))
        if not is_binary:
            raise Exception(result.Error)


def _validate_privacy_value(field: str, raw: str) -> str:
    allowed = {e.value for e in PrivacySetting}
    val = raw.lower().strip()
    if val not in allowed:
        raise HTTPException(
            status_code=422,
            detail={"error": "INVALID_FIELD", "message": f"Invalid value for '{field}': '{raw}'. Accepted: {', '.join(sorted(allowed - {''}))}."},
        )
    return val


async def _set_privacy_route(field: str, raw_value: Optional[str]) -> dict:
    if raw_value is None:
        return await _get_current_privacy(field)
    sock = _require_client()
    val = _validate_privacy_value(field, raw_value)
    pstype = _FIELD_TO_TYPE[field]
    try:
        await asyncio.to_thread(_set_privacy_direct, sock, pstype, PrivacySetting(val))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set privacy {field}: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
    logger.info(f"⚙️ Privacy {field}: {val}")
    return {"success": True, "updated": field, "value": val}


async def set_last_seen(data: PrivacyValueRequest):
    return await _set_privacy_route("lastSeen", data.value)


async def set_online(data: PrivacyValueRequest):
    return await _set_privacy_route("online", data.value)


async def set_profile(data: PrivacyValueRequest):
    return await _set_privacy_route("profile", data.value)


async def set_status(data: PrivacyValueRequest):
    return await _set_privacy_route("status", data.value)


async def set_read_receipts(data: PrivacyValueRequest):
    return await _set_privacy_route("readReceipts", data.value)


async def set_groups_add(data: PrivacyValueRequest):
    return await _set_privacy_route("groupsAdd", data.value)


async def set_call_add(data: PrivacyValueRequest):
    return await _set_privacy_route("callAdd", data.value)


async def set_about(data: AboutRequest):
    if data.value is None:
        return {"success": True, "field": "about", "value": None}
    sock = _require_client()
    try:
        await asyncio.to_thread(sock.set_status_message, data.value)
    except Exception as e:
        logger.error(f"Failed to set about: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
    logger.info("⚙️ Privacy about updated")
    return {"success": True, "updated": "about", "value": data.value}


async def set_disappearing_timer(data: DisappearingTimerRequest):
    if data.value is None:
        return {"success": True, "field": "disappearingTimer", "value": None}
    sock = _require_client()
    try:
        if data.value == 0:
            await asyncio.to_thread(sock.set_default_disappearing_timer, 0)
            logger.info("⚙️ Disappearing messages: off")
            return {"success": True, "updated": "disappearingTimer", "value": "off"}
        duration = timedelta(hours=data.value)
        await asyncio.to_thread(sock.set_default_disappearing_timer, duration)
    except Exception as e:
        logger.error(f"Failed to set disappearing timer: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
    logger.info(f"⚙️ Disappearing messages: {data.value}h")
    return {"success": True, "updated": "disappearingTimer", "value": f"{data.value}h"}
