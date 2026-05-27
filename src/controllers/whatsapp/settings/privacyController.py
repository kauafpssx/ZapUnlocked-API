import asyncio
from datetime import timedelta
from fastapi import HTTPException
from neonize.utils.enum import PrivacySettingType, PrivacySetting
from src.services.whatsapp.client import get_sock
from src.utils.logger import logger
from src.controllers.whatsapp.schemas import PrivacyUpdateRequest


# ── Mapeamento campo do schema → PrivacySettingType ────────
_FIELD_TO_TYPE = {
    "lastSeen": PrivacySettingType.LAST_SEEN,
    "online": PrivacySettingType.ONLINE,
    "profile": PrivacySettingType.PROFILE,
    "status": PrivacySettingType.STATUS,
    "readReceipts": PrivacySettingType.READ_RECEIPTS,
    "groupsAdd": PrivacySettingType.GROUP_ADD,
    "callAdd": PrivacySettingType.CALL_ADD,
}

# ── Mapeamento campo do schema → label (log) ────────────────
_FIELD_LABEL = {
    "lastSeen": "Visto por último",
    "online": "Online",
    "profile": "Privacidade da foto",
    "status": "Privacidade do status",
    "readReceipts": "Confirmação de leitura",
    "groupsAdd": "Adição em grupos",
    "callAdd": "Adição em chamadas",
    "about": "Recado (about)",
    "disappearingTimer": "Mensagens temporárias",
}


def _set_privacy(sock, field: str, value: str):
    """Aplica uma configuração de privacidade via Neonize."""
    pstype = _FIELD_TO_TYPE.get(field)
    if not pstype:
        return
    psvalue = PrivacySetting(value.lower().strip())
    sock.set_privacy_setting(pstype, psvalue)


async def update_privacy(data: PrivacyUpdateRequest):
    try:
        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail="WhatsApp não conectado")

        updates = []

        # ── Privacidades via set_privacy_setting ─────────────
        for field, pstype in _FIELD_TO_TYPE.items():
            raw = getattr(data, field, None)
            if raw:
                allowed = {e.value for e in PrivacySetting}
                val = raw.lower().strip()
                if val not in allowed:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Valor inválido para '{field}': '{raw}'. "
                               f"Valores aceitos: {', '.join(sorted(allowed - {''}))}",
                    )
                await asyncio.to_thread(_set_privacy, sock, field, val)
                updates.append(f"{_FIELD_LABEL[field]}: {val}")

        # ── Recado (about / status message) ──────────────────
        if data.about is not None:
            await asyncio.to_thread(sock.set_status_message, data.about)
            updates.append(f"{_FIELD_LABEL['about']}: {data.about}")

        # ── Mensagens temporárias ────────────────────────────
        if data.disappearingTimer is not None:
            if data.disappearingTimer == 0:
                await asyncio.to_thread(sock.set_default_disappearing_timer, 0)
                updates.append(f"{_FIELD_LABEL['disappearingTimer']}: desligado")
            else:
                duration = timedelta(hours=data.disappearingTimer)
                await asyncio.to_thread(sock.set_default_disappearing_timer, duration)
                updates.append(f"{_FIELD_LABEL['disappearingTimer']}: {data.disappearingTimer}h")

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="Nenhum parâmetro fornecido. Envie pelo menos um campo para atualizar.",
            )

        logger.info(f"⚙️ Privacidade atualizada: {', '.join(updates)}")
        return {"success": True, "updated": updates}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar privacidade: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
