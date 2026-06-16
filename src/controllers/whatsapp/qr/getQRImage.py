from src.utils.decorators import get_session_id
from fastapi import HTTPException, Request, Response
import io
import qrcode
from src.services.whatsapp import state as _wa_state
from src.services.whatsapp.client import activate_qr

async def get_qr_image(request: Request = None):
    sid = get_session_id(request)
    activate_qr(sid)
    qr = _wa_state.get_qr(sid)

    if not qr:
        message = "WhatsApp is already connected." if _wa_state.get_is_ready(sid) else "Waiting for QR code generation..."
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": message})

    try:
        img = qrcode.make(qr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        expires_in = _wa_state.get_qr_expires_in(sid)
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-QR-Expires-In": str(expires_in) if expires_in is not None else "0",
        }
        return Response(content=buf.getvalue(), media_type="image/png", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
