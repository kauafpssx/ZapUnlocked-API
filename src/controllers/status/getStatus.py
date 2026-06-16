from __future__ import annotations

import asyncio
import base64
import io
import json
import platform
import sys
import time
from datetime import datetime, timezone

import psutil
import qrcode

from fastapi import Request
from src.utils.decorators import get_session_id
from src.services.whatsapp import state as _wa_state
from src.services.whatsapp.client import activate_qr
from src.utils.dry_run import is_dry_run

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
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


async def get_status_controller(request: Request = None) -> dict:
    sid = get_session_id(request)
    process = psutil.Process()
    mem = process.memory_info()
    sysmem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    uptime_s = time.time() - _START_TIME
    wa_ready = _wa_state.get_is_ready(sid)

    proc_cpu = process.cpu_percent(interval=None)
    sys_cpu = psutil.cpu_percent(interval=None)

    health = "ok" if wa_ready else "degraded"

    return {
        "status": health,
        "dryRun": is_dry_run(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": _fmt_uptime(uptime_s),
        "uptime_seconds": int(uptime_s),
        "whatsapp": {
            "connected": wa_ready,
            "qr_pending": _wa_state.get_qr(sid) is not None and not wa_ready,
        },
        "process": {
            "pid": process.pid,
            "threads": process.num_threads(),
            "cpu_percent": proc_cpu,
        },
        "system": {
            "cpu_percent": sys_cpu,
            "cpu_cores": psutil.cpu_count(logical=True),
            "memory": {
                "total": _fmt_mb(sysmem.total),
                "used": _fmt_mb(sysmem.used),
                "process_rss": _fmt_mb(mem.rss),
                "process_vms": _fmt_mb(mem.vms),
                "percent": sysmem.percent,
            },
            "disk": {
                "total": _fmt_gb(disk.total),
                "used": _fmt_gb(disk.used),
                "free": _fmt_gb(disk.free),
                "percent": disk.percent,
            },
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "arch": platform.machine(),
        },
    }


def _generate_qr_b64(qr_data: str) -> str:
    img = qrcode.make(qr_data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _try_refresh_qr(qr: str | None, is_ready: bool, expires_in: int | None, last_refreshed: str | None, session_id: str = "1") -> str | None:
    if not (qr and not is_ready and expires_in is not None and expires_in <= 0):
        return None
    if last_refreshed == qr:
        return last_refreshed
    _wa_state.set_current_qr(None, session_id)
    _wa_state.set_qr_last_generated_at(None, session_id)
    activate_qr(session_id)
    return qr


async def _build_sse_data(qr: str | None, is_ready: bool, expires_in: int | None) -> dict:
    data = {
        "state": "CONNECTED" if is_ready else "AWAITING_QR",
        "qr_string": qr if qr else None,
        "qr": None,
        "qr_expires_in": expires_in,
    }
    if qr and not is_ready and expires_in and expires_in > 0:
        try:
            data["qr"] = await asyncio.to_thread(_generate_qr_b64, qr)
        except Exception:
            pass
    return data


async def stream_status_generator(request):
    sid = get_session_id(request)
    last_refreshed_qr: str | None = None
    # Subscribing to the stream counts as authenticated access — unlock QR gate
    if not _wa_state.get_is_ready(sid):
        activate_qr(sid)
    while True:
        if await request.is_disconnected():
            break
        qr = _wa_state.get_qr(sid)
        is_ready = _wa_state.get_is_ready(sid)
        expires_in = _wa_state.get_qr_expires_in(sid) if qr and not is_ready else None
        refreshed = _try_refresh_qr(qr, is_ready, expires_in, last_refreshed_qr, sid)
        if refreshed is not None:
            last_refreshed_qr = refreshed
        else:
            last_refreshed_qr = None
        data = await _build_sse_data(qr, is_ready, expires_in)
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(2)


async def stream_status_controller(request):
    from fastapi.responses import StreamingResponse
    return StreamingResponse(stream_status_generator(request), media_type="text/event-stream")
