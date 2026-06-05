import gc
import psutil
from fastapi import Query


async def get_memory_status(run_gc: bool = Query(default=False, alias="gc")):
    if run_gc:
        gc.collect()

    process = psutil.Process()
    mem = process.memory_info()
    sysmem = psutil.virtual_memory()

    def fmt_mb(b):
        return f"{b / 1024 / 1024:.2f} MB"

    return {
        "success": True,
        "process": {
            "rss": fmt_mb(mem.rss),
            "vms": fmt_mb(mem.vms),
        },
        "system": {
            "total": fmt_mb(sysmem.total),
            "used": fmt_mb(sysmem.used),
            "free": fmt_mb(sysmem.available),
            "percent": sysmem.percent,
        },
    }
