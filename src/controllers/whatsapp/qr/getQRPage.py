import base64
import io
import qrcode
from fastapi import Request
from fastapi.responses import HTMLResponse
from pathlib import Path
from src.services.whatsapp.client import get_qr, get_is_ready
from src.config.constants import BASE_DIR

async def get_qr_page(request: Request):
    qr = get_qr()
    is_connected = get_is_ready()
    api_key = request.query_params.get("API_KEY", "")

    try:
        qr_data_url = None
        if qr:
            img = qrcode.make(qr)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            qr_data_url = f"data:image/png;base64,{b64}"

        template_path = Path(BASE_DIR) / "src" / "views" / "qr.html"

        if not template_path.exists():
            return HTMLResponse("<h1>Template não encontrado</h1>", status_code=500)

        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        status_text = "Conectado" if is_connected else ("Aguardando Scan" if qr_data_url else "Inicializando")
        title_text = "Conectado!" if is_connected else ("📲 Escaneie o QR" if qr_data_url else "⏳ Inicializando...")
        desc_text = "O assistente está pronto." if is_connected else "Abra o WhatsApp e escaneie o código abaixo."
        qr_hidden_class = "hidden" if is_connected else ""
        instr_hidden_class = "" if not is_connected else "hidden"
        instr_hidden_class_inverse = "hidden" if not is_connected else ""
        qr_content = f'<img src="{qr_data_url}" id="qr-img">' if qr_data_url else '<div class="loader"></div>'

        html = html.replace("{{STATUS_TEXT}}", status_text)
        html = html.replace("{{TITLE_TEXT}}", title_text)
        html = html.replace("{{DESC_TEXT}}", desc_text)
        html = html.replace("{{QR_HIDDEN_CLASS}}", qr_hidden_class)
        html = html.replace("{{INSTR_HIDDEN_CLASS}}", instr_hidden_class)
        html = html.replace("{{INSTR_HIDDEN_CLASS_INVERSE}}", instr_hidden_class_inverse)
        html = html.replace("{{QR_CONTENT}}", qr_content)
        html = html.replace("{{API_KEY}}", api_key)
        html = html.replace("{{IS_CONNECTED}}", str(is_connected).lower())

        return HTMLResponse(content=html)
    except Exception as e:
        return HTMLResponse(f"<h1>Erro ao gerar QR Code</h1><p>{str(e)}</p>", status_code=500)
