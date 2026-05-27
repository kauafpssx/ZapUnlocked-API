"""Controller para configurações da instância (renomear, etc)."""

import asyncio
import json
from fastapi import HTTPException
from src.config.constants import data_dir
from src.controllers.whatsapp.schemas import UpdateInstanceNameRequest
from src.services.whatsapp.client import get_sock
from src.utils.logger import logger


async def update_instance_name(data: UpdateInstanceNameRequest):
    """Renomeia a instância no arquivo db_config.json + WhatsApp pushname."""
    try:
        # ── Atualiza pushname no WhatsApp ────────────────────
        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail="WhatsApp não conectado")
        await asyncio.to_thread(sock.set_profile_name, data.name)

        # ── Persiste nome localmente ─────────────────────────
        db_config_file = data_dir / "db_config.json"
        current = {}
        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                current.update(json.load(f))
        current["instanceName"] = data.name
        with open(db_config_file, "w") as f:
            json.dump(current, f)

        logger.info(f"📛 Instância renomeada para: {data.name}")
        return {
            "status": "success",
            "message": f"Instância renomeada para: {data.name}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao renomear instância: {str(e)}"
        )
