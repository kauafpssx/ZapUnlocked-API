from src.utils.decorators import get_session_id
import asyncio
import json
from fastapi import HTTPException, Request
from src.config.constants import get_data_dir
from src.schemas import UpdateInstanceNameRequest
from src.services.whatsapp import state
from src.utils.logger import logger
from pathlib import Path


async def update_instance_name(data: UpdateInstanceNameRequest, request: Request = None):
    sid = get_session_id(request)
    try:
        sock = state.get_client(sid)
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})
        await asyncio.to_thread(sock.set_profile_name, data.name)

        db_config_file = Path(get_data_dir(sid)) / "db_config.json"
        current = {}
        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                current.update(json.load(f))
        current["instanceName"] = data.name
        db_config_file.parent.mkdir(parents=True, exist_ok=True)
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
