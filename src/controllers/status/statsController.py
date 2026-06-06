import time
from src.services.whatsapp import state
from src.services.stats import get_all, reset as reset_stats


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
