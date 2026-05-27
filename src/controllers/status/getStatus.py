from datetime import datetime
from src.services.whatsapp.client import get_is_ready, get_qr

async def get_status_controller():
    return {
        "status": "online",
        "whatsapp": "connected" if get_is_ready() else "disconnected",
        "qr": get_qr(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

async def stream_status_generator(request):
    from fastapi import Request
    import json
    import asyncio
    import io
    import qrcode
    import base64

    def _generate_qr_b64(qr_data):
        img = qrcode.make(qr_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    while True:
        if await request.is_disconnected():
            break

        qr = get_qr()
        is_ready = get_is_ready()
        
        data = {
            "state": "CONNECTED" if is_ready else "AWAITING_QR",
            "qr_string": qr if qr else None,
            "qr": None
        }

        if qr and not is_ready:
            try:
                # Offload CPU-bound qrcode generation to avoid event loop deadlock
                data["qr"] = await asyncio.to_thread(_generate_qr_b64, qr)
            except Exception:
                pass

        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(2)

async def stream_status_controller(request):
    from fastapi import Request
    from fastapi.responses import StreamingResponse
    return StreamingResponse(stream_status_generator(request), media_type="text/event-stream")
