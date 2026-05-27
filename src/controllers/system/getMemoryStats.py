import psutil
import gc
from fastapi import Request

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
        "uptime": f"{int(process.create_time())} s", # Using creation time as a pseudo uptime for the process
    }

    return stats
