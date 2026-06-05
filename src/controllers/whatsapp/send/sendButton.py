from fastapi import HTTPException
from src.services.whatsapp.sender import send_button_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.utils.logger import logger
from src.utils.security.callback_token import create_callback_payload
from src.utils.quote import build_send_options
from src.utils.formatter import format_text
from src.schemas import (
    SendButtonRequest,
    SendButtonOtpRequest,
    SendButtonPixRequest,
    SendButtonQuickReplyRequest,
    SendButtonUrlRequest,
    SendButtonCallRequest,
)


@require_whatsapp
@handle_errors("send button")
async def send_with_buttons(data: SendButtonRequest):
    jid = f"{data.phone}@s.whatsapp.net"

    options = await build_send_options(
        jid,
        reply_identifier=data.reply or data.quoted_id,
        reply_type=data.type or "id",
        delay_message=data.delay_message,
        delay_typing=data.delay_typing,
        mentioned=data.mentioned,
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
                "buttonText": format_text(btn.get("buttonText", btn.get("text", "Button"))),
                "id": btn_id,
            }
            buttons_to_send.append(btn_dict)
    elif data.code:
        # OTP (Copy Code)
        buttons_to_send.append({
            "type": "otp",
            "text": data.button_text or "Copy code",
            "code": data.code
        })
    elif data.pixKey:
        # PIX
        buttons_to_send.append({
            "type": "pix",
            "pixKey": data.pixKey,
            "pixType": data.pixType or data.type or "EVP",
            "pixValue": data.pixValue,
            "merchantName": data.merchantName or "",
            "pixCity": data.pixCity or "",
            "pixDescription": data.pixDescription or "",
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
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "At least one button must be provided."})


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
    return {"success": True, "message": "Interactive message sent."}


@require_whatsapp
@handle_errors("send otp")
async def send_otp(data: SendButtonOtpRequest):
    jid = f"{data.phone}@s.whatsapp.net"
    options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    formatted_text = format_text(data.text or "")
    buttons = [{"type": "otp", "text": data.button_text or "Copy code", "code": data.code}]
    await send_button_message(jid, formatted_text, buttons, options, title=data.title or "", footer=data.footer or "", image_url=data.image)
    return {"success": True, "message": "OTP message sent."}


@require_whatsapp
@handle_errors("send pix")
async def send_pix(data: SendButtonPixRequest):
    jid = f"{data.phone}@s.whatsapp.net"
    options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    formatted_text = format_text(data.text or "")
    ptype = (data.pixType or "EVP").upper()
    footer = data.footer or f"{ptype}: {data.pixKey}"
    buttons = [{
        "type": "pix",
        "pixKey": data.pixKey,
        "pixType": data.pixType or "EVP",
        "pixValue": data.pixValue,
        "merchantName": data.merchantName,
        "pixCity": data.pixCity or "",
        "pixDescription": data.pixDescription or "",
        "text": data.button_text or "Pagar",
    }]
    await send_button_message(jid, formatted_text, buttons, options, title=data.title or "", footer=footer, image_url=data.image)
    return {"success": True, "message": "PIX message sent."}


@require_whatsapp
@handle_errors("send quick reply")
async def send_quick_reply(data: SendButtonQuickReplyRequest):
    jid = f"{data.phone}@s.whatsapp.net"
    options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    formatted_text = format_text(data.text or "")
    buttons = []
    for i, btn in enumerate(data.buttons):
        btn_id = btn.get("id", btn.get("buttonId", f"btn_{i}"))
        webhook = btn.get("webhook")
        reaction = btn.get("reaction")
        if webhook or reaction:
            token = create_callback_payload({**(webhook or {}), "reaction": reaction or (webhook.get("reaction") if webhook else None)})
            btn_id = f"cb={token}"
        buttons.append({"type": "quick_reply", "buttonText": format_text(btn.get("text", btn.get("buttonText", f"Button {i}"))), "id": btn_id})
    await send_button_message(jid, formatted_text, buttons, options, title=data.title or "", footer=data.footer or "", image_url=data.image)
    return {"success": True, "message": "Quick reply message sent."}


@require_whatsapp
@handle_errors("send url button")
async def send_url(data: SendButtonUrlRequest):
    jid = f"{data.phone}@s.whatsapp.net"
    options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    formatted_text = format_text(data.text or "")
    buttons = [{"type": "url", "url": data.url, "text": data.button_text or "Acessar", "buttonText": data.button_text or "Acessar"}]
    await send_button_message(jid, formatted_text, buttons, options, title=data.title or "", footer=data.footer or "", image_url=data.image)
    return {"success": True, "message": "URL button message sent."}


@require_whatsapp
@handle_errors("send call button")
async def send_call(data: SendButtonCallRequest):
    jid = f"{data.phone}@s.whatsapp.net"
    options = await build_send_options(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id", delay_message=data.delay_message, delay_typing=data.delay_typing, mentioned=data.mentioned)
    formatted_text = format_text(data.text or "")
    buttons = [{"type": "call", "phoneNumber": data.callPhone, "text": data.button_text or "Ligar", "buttonText": data.button_text or "Ligar"}]
    await send_button_message(jid, formatted_text, buttons, options, title=data.title or "", footer=data.footer or "", image_url=data.image)
    return {"success": True, "message": "Call button message sent."}
