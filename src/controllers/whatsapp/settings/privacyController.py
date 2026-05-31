import asyncio
from datetime import timedelta
from fastapi import HTTPException
from neonize.utils.enum import PrivacySettingType, PrivacySetting
from src.services.whatsapp.client import get_client
from src.utils.logger import logger
from src.schemas import PrivacyUpdateRequest


# ── Schema field → PrivacySettingType mapping ────────
_FIELD_TO_TYPE = {
    "lastSeen": PrivacySettingType.LAST_SEEN,
    "online": PrivacySettingType.ONLINE,
    "profile": PrivacySettingType.PROFILE,
    "status": PrivacySettingType.STATUS,
    "readReceipts": PrivacySettingType.READ_RECEIPTS,
    "groupsAdd": PrivacySettingType.GROUP_ADD,
    "callAdd": PrivacySettingType.CALL_ADD,
}

# ── Schema field → log label mapping ────────────────
_FIELD_LABEL = {
    "lastSeen": "Last seen",
    "online": "Online",
    "profile": "Profile photo privacy",
    "status": "Status privacy",
    "readReceipts": "Read receipts",
    "groupsAdd": "Group add",
    "callAdd": "Call add",
    "about": "About (status message)",
    "disappearingTimer": "Disappearing messages",
}


def _set_privacy(sock, field: str, value: str):
    """Apply a privacy setting via Neonize."""
    pstype = _FIELD_TO_TYPE.get(field)
    if not pstype:
        return
    psvalue = PrivacySetting(value.lower().strip())
    sock.set_privacy_setting(pstype, psvalue)


async def update_privacy(data: PrivacyUpdateRequest):
    try:
        sock = get_client()
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

        updates = []

        # ── Privacy via set_privacy_setting ─────────────────
        for field, pstype in _FIELD_TO_TYPE.items():
            raw = getattr(data, field, None)
            if raw:
                allowed = {e.value for e in PrivacySetting}
                val = raw.lower().strip()
                if val not in allowed:
                    raise HTTPException(
                        status_code=422,
                        detail={"error": "INVALID_FIELD", "message": f"Invalid value for '{field}': '{raw}'. Accepted values: {', '.join(sorted(allowed - {''}))}."},
                    )
                await asyncio.to_thread(_set_privacy, sock, field, val)
                updates.append(f"{_FIELD_LABEL[field]}: {val}")

        # ── About / status message ──────────────────
        if data.about is not None:
            await asyncio.to_thread(sock.set_status_message, data.about)
            updates.append(f"{_FIELD_LABEL['about']}: {data.about}")

        # ── Disappearing messages ────────────────────────────
        if data.disappearingTimer is not None:
            if data.disappearingTimer == 0:
                await asyncio.to_thread(sock.set_default_disappearing_timer, 0)
                updates.append(f"{_FIELD_LABEL['disappearingTimer']}: off")
            else:
                duration = timedelta(hours=data.disappearingTimer)
                await asyncio.to_thread(sock.set_default_disappearing_timer, duration)
                updates.append(f"{_FIELD_LABEL['disappearingTimer']}: {data.disappearingTimer}h")

        if not updates:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_FIELD", "message": "No parameters provided. Send at least one field to update."},
            )

        logger.info(f"⚙️ Privacy updated: {', '.join(updates)}")
        return {"success": True, "updated": updates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update privacy settings: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
