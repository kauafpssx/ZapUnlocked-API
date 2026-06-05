from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready


async def readiness_controller() -> dict:
    if get_is_ready():
        return {"ready": True}
    raise HTTPException(
        status_code=503,
        detail={"ready": False, "reason": "whatsapp_not_connected"},
    )
