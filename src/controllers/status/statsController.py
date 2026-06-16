from src.utils.decorators import get_session_id
import time
from fastapi import HTTPException, Request
from src.services.whatsapp import state
from src.services.stats import get_all, reset as reset_stats, get_webhook_stats, reset_webhook_stats


def _sid(request: Request) -> str:
    return get_session_id(request)


async def get_stats(request: Request):
    sid = _sid(request)
    counters = get_all(sid)
    now = time.time()

    start = state.get_start_time(sid)
    uptime_seconds = int(now - start)

    connected_at = state.get_connected_at(sid)
    connected_seconds = int(now - connected_at) if connected_at else None

    return {
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": _fmt(uptime_seconds),
        },
        "connected": {
            "seconds": connected_seconds,
            "formatted": _fmt(connected_seconds) if connected_seconds is not None else None,
        },
        "messages": {
            "sent": counters["messages_sent"],
            "received": counters["messages_received"],
        },
        "webhooks": {
            "fired": counters["webhooks_fired"],
        },
    }


async def delete_stats(request: Request):
    sid = _sid(request)
    reset_stats(sid)
    return {"success": True, "message": "Stats reset."}


async def get_webhook_stats_controller(request: Request, name: str = None):
    sid = _sid(request)
    if name is not None:
        entry = get_webhook_stats(name, sid)
        if entry is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"No stats for webhook '{name}'."})
        return {"name": name, **entry}
    all_stats = get_webhook_stats(session_id=sid)
    return {
        "total": len(all_stats),
        "webhooks": [{"name": n, **v} for n, v in all_stats.items()],
    }


async def delete_webhook_stats_controller(request: Request, name: str = None):
    sid = _sid(request)
    if name is not None:
        if get_webhook_stats(name, sid) is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"No stats for webhook '{name}'."})
        reset_webhook_stats(name, sid)
        return {"success": True, "message": f"Stats for '{name}' reset."}
    reset_webhook_stats(session_id=sid)
    return {"success": True, "message": "All webhook stats reset."}


def _fmt(seconds: int) -> str:
    if seconds is None:
        return None
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
