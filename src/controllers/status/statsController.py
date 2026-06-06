import time
from fastapi import HTTPException
from src.services.whatsapp import state
from src.services.stats import get_all, reset as reset_stats, get_webhook_stats, reset_webhook_stats


async def get_stats():
    counters = get_all()
    now = time.time()

    start = state.get_start_time()
    uptime_seconds = int(now - start)

    connected_at = state.get_connected_at()
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


async def delete_stats():
    reset_stats()
    return {"success": True, "message": "Stats reset."}


async def get_webhook_stats_controller(name: str = None):
    if name is not None:
        entry = get_webhook_stats(name)
        if entry is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"No stats for webhook '{name}'."})
        return {"name": name, **entry}
    all_stats = get_webhook_stats()
    return {
        "total": len(all_stats),
        "webhooks": [{"name": n, **v} for n, v in all_stats.items()],
    }


async def delete_webhook_stats_controller(name: str = None):
    if name is not None:
        if get_webhook_stats(name) is None:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"No stats for webhook '{name}'."})
        reset_webhook_stats(name)
        return {"success": True, "message": f"Stats for '{name}' reset."}
    reset_webhook_stats()
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
