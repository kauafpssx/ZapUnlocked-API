from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from src.services.whatsapp import state


async def readiness_controller(request: Request = None) -> dict:
    sid = get_session_id(request)
    if state.get_is_ready(sid):
        return {"ready": True}
    raise HTTPException(
        status_code=503,
        detail={"ready": False, "reason": "whatsapp_not_connected"},
    )
