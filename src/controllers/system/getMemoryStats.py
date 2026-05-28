import time
import psutil
import gc
from fastapi import Request

def _fmt_uptime(seconds: float) -> str:
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

from src.services.whatsapp.client import get_store

async def get_memory_stats(request: Request):
    if request.query_params.get("gc") == "true":
        gc.collect()

    process = psutil.Process()
    mem_info = process.memory_info()
    sys_mem = psutil.virtual_memory()

    contacts_count = 0 # Depreciado para economizar RAM

    def format_mb(bytes_val):
        return f"{(bytes_val / 1024 / 1024):.2f} MB"

    stats = {
        "process": {
            "rss": format_mb(mem_info.rss),
            "vms": format_mb(mem_info.vms),
        },
        "whatsapp": {
            "contactsInMemory": contacts_count
        },
        "system": {
            "total": format_mb(sys_mem.total),
            "free": format_mb(sys_mem.available),
            "usagePercent": f"{sys_mem.percent}%"
        },
        "uptime": _fmt_uptime(time.time() - process.create_time()),
    }

    return stats
