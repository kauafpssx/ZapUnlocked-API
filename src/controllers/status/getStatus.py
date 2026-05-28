import time
import platform
import sys
import psutil
from datetime import datetime, timezone

from src.services.whatsapp.client import get_is_ready, get_qr

_START_TIME = time.time()

def _fmt_mb(b: int) -> str:
    return f"{b / 1024 / 1024:.2f} MB"

def _fmt_gb(b: int) -> str:
    return f"{b / 1024 / 1024 / 1024:.2f} GB"

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

async def get_status_controller():
    process = psutil.Process()
    mem  = process.memory_info()
    sysmem = psutil.virtual_memory()
    disk   = psutil.disk_usage("/")

    uptime_s = time.time() - _START_TIME
    wa_ready = get_is_ready()

    # cpu_percent(None) = non-blocking, since last call
    proc_cpu = process.cpu_percent(interval=None)
    sys_cpu  = psutil.cpu_percent(interval=None)

    health = "ok" if wa_ready else "degraded"

    return {
        "status": health,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": _fmt_uptime(uptime_s),
        "uptime_seconds": int(uptime_s),
        "whatsapp": {
            "connected": wa_ready,
            "qr_pending": get_qr() is not None and not wa_ready,
        },
        "process": {
            "pid": process.pid,
            "threads": process.num_threads(),
            "cpu_percent": proc_cpu,
            "memory_rss": _fmt_mb(mem.rss),
            "memory_vms": _fmt_mb(mem.vms),
        },
        "system": {
            "cpu_percent": sys_cpu,
            "cpu_cores": psutil.cpu_count(logical=True),
            "memory_total": _fmt_mb(sysmem.total),
            "memory_used": _fmt_mb(sysmem.used),
            "memory_percent": sysmem.percent,
            "disk_total": _fmt_gb(disk.total),
            "disk_used": _fmt_gb(disk.used),
            "disk_free": _fmt_gb(disk.free),
            "disk_percent": disk.percent,
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "arch": platform.machine(),
        },
    }


async def stream_status_generator(request):
    import json
    import asyncio
    import io
    import qrcode
    import base64

    def _generate_qr_b64(qr_data):
        img = qrcode.make(qr_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    while True:
        if await request.is_disconnected():
            break

        qr = get_qr()
        is_ready = get_is_ready()

        data = {
            "state": "CONNECTED" if is_ready else "AWAITING_QR",
            "qr_string": qr if qr else None,
            "qr": None,
        }

        if qr and not is_ready:
            try:
                data["qr"] = await asyncio.to_thread(_generate_qr_b64, qr)
            except Exception:
                pass

        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(2)


async def stream_status_controller(request):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(stream_status_generator(request), media_type="text/event-stream")
