from fastapi import HTTPException, Response
import io
import qrcode
from src.services.whatsapp.client import get_qr, get_is_ready, activate_qr, get_qr_expires_in

async def get_qr_image():
    activate_qr()
    qr = get_qr()

    if not qr:
        message = "WhatsApp já está conectado" if get_is_ready() else "Aguardando geração do QR Code..."
        raise HTTPException(status_code=404, detail={"error": "QR Code não disponível", "message": message})

    try:
        img = qrcode.make(qr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        expires_in = get_qr_expires_in()
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-QR-Expires-In": str(expires_in) if expires_in is not None else "0",
        }
        return Response(content=buf.getvalue(), media_type="image/png", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Erro ao gerar QR Code", "message": str(e)})
