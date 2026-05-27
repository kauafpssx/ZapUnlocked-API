from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_button_message
from src.utils.logger import logger
from src.utils.callbackUtils import create_callback_payload
from src.utils.quote import resolve_quote
from src.utils.formatter import format_text
from ..schemas import SendButtonRequest


async def send_with_buttons(data: SendButtonRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        options = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        # 2. Extract and format text
        message_text = data.text or data.message or ""
        formatted_text = format_text(message_text)

        # 3. Build buttons list (handling legacy and new format)
        buttons_to_send = []

        if data.buttons:
            # Modern format (list of buttons)
            for btn in data.buttons:
                btn_id = btn.get("id", btn.get("buttonId", "reply_button"))
                webhook = btn.get("webhook")
                reaction = btn.get("reaction")

                if webhook or reaction:
                    token = create_callback_payload({
                        **(webhook or {}),
                        "reaction": reaction or (webhook.get("reaction") if webhook else None),
                    })
                    btn_id = f"cb={token}"

                btn_dict = {
                    **btn,
                    "buttonText": format_text(btn.get("buttonText", btn.get("text", "Botão"))),
                    "id": btn_id,
                }
                buttons_to_send.append(btn_dict)
        elif data.code:
            # OTP (Copy Code)
            buttons_to_send.append({
                "type": "otp",
                "text": data.button_text or "Copiar código",
                "code": data.code
            })
        elif data.pixKey:
            # PIX
            buttons_to_send.append({
                "type": "pix",
                "text": data.button_text or "💰 Copiar PIX",
                "pixKey": data.pixKey,
                "pixType": data.pixType or data.type or "EVP"
            })
        elif data.button_text:
            # Legacy format (single button fields)
            btn_id = data.button_id or data.button_value or "reply_button"
            if data.webhook or data.reaction:
                token = create_callback_payload({
                    **(data.webhook or {}),
                    "reaction": data.reaction or (data.webhook.get("reaction") if data.webhook else None),
                })
                btn_id = f"cb={token}"

            buttons_to_send.append({
                "buttonText": format_text(data.button_text),
                "id": btn_id
            })

        if not buttons_to_send:
            raise HTTPException(status_code=400, detail="Pelo menos um botão deve ser informado.")


        # 4. Auto-generate footer for PIX if missing
        final_footer = data.footer or ""
        if not final_footer:
            for btn in buttons_to_send:
                if btn.get("type") == "pix" and btn.get("pixKey"):
                    ptype = btn.get("pixType", "PIX").upper()
                    pkey = btn.get("pixKey")
                    final_footer = f"{ptype}: {pkey}"
                    break

        await send_button_message(
            jid, 
            formatted_text, 
            buttons_to_send, 
            options,
            title=data.title or "",
            footer=final_footer,
            image_url=data.image
        )
        return {"success": True, "message": "Mensagem interativa enviada ✅"}
    except Exception as e:
        logger.error(f"❌ Erro ao enviar com botão: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
