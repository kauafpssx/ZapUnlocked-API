"""Controller for instance settings (rename, etc)."""

import asyncio
import json
from fastapi import HTTPException
from src.config.constants import data_dir
from src.controllers.whatsapp.schemas import UpdateInstanceNameRequest
from src.services.whatsapp.client import get_sock
from src.utils.logger import logger


async def update_instance_name(data: UpdateInstanceNameRequest):
    """Rename the instance in db_config.json and update WhatsApp pushname."""
    try:
        # ── Atualiza pushname no WhatsApp ────────────────────
        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
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

        logger.info(f"📛 Instance renamed to: {data.name}")
        return {
            "success": True,
            "message": f"Instance renamed to: {data.name}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to rename instance: {str(e)}"}
        )
