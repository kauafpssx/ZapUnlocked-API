from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request
from pydantic import BaseModel
from src.services.whatsapp.db_cleanup import cleanup_db, set_cleanup_interval, get_cleanup_state
from src.utils.logger import logger


class ConfigRequest(BaseModel):
    interval: int


async def manual_cleanup(request: Request):
    sid = get_session_id(request)
    try:
        cleanup_db(sid)
        return {"success": True, "message": "Manual cleanup completed successfully."}
    except Exception as e:
        logger.error(f"Manual cleanup error: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def update_config(data: ConfigRequest, request: Request):
    sid = get_session_id(request)
    try:
        set_cleanup_interval(data.interval, sid)
        return {"success": True, "message": f"Cleanup interval updated to {data.interval} minutes."}
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def get_status(request: Request):
    sid = get_session_id(request)
    st = get_cleanup_state(sid)
    now = int(__import__("time").time())
    lct = st["last_cleanup_time"]
    ci = st["current_interval"]

    next_run = lct + (ci * 60)
    time_remaining = max(0, next_run - now)
    minutes = time_remaining // 60
    seconds = time_remaining % 60

    return {
        "last_run": lct,
        "next_run": next_run,
        "interval": ci,
        "time_remaining_seconds": time_remaining,
        "time_remaining_human": f"{minutes}m {seconds}s",
    }
