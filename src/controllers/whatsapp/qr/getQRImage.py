from fastapi import HTTPException, Response
import io
import qrcode
from src.services.whatsapp.client import get_qr, get_is_ready

async def get_qr_image():
    qr = get_qr()

    if not qr:
        message = "WhatsApp já está conectado" if get_is_ready() else "Aguardando geração do QR Code..."
        raise HTTPException(status_code=404, detail={"error": "QR Code não disponível", "message": message})

    try:
        img = qrcode.make(qr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        return Response(content=buf.getvalue(), media_type="image/png", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Erro ao gerar QR Code", "message": str(e)})
