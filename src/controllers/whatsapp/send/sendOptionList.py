from fastapi import HTTPException
from src.services.whatsapp.sender import send_button_message
from src.utils.decorators import require_whatsapp, handle_errors
from src.utils.quote import resolve_quote
from src.utils.formatter import format_text
from src.utils.logger import logger
from src.schemas import SendOptionListRequest


@require_whatsapp
@handle_errors("send option list")
async def send_option_list(data: SendOptionListRequest):
    raise HTTPException(
        status_code=503,
        detail={
            "error": "ROUTE_DISABLED",
            "message": "This route is temporarily disabled. Option list messages are not supported on Android and iOS at this time."
        }
    )

    jid = f"{data.phone}@s.whatsapp.net"

    options = await resolve_quote(
        jid,
        reply_identifier=data.quoted_id,
        reply_type=data.type or "id",
    )

    message_text = data.text or data.message or ""
    formatted_text = format_text(message_text)

    sections = data.sections
    button_label = data.button_text or "Ver opções"
    if not sections and data.buttons:
        for btn in data.buttons:
            if btn.get("type") == "list" and btn.get("sections"):
                sections = btn["sections"]
                button_label = btn.get("buttonText") or btn.get("text") or button_label
                break

    if not sections:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "Provide 'sections' or 'buttons' with type 'list' and sections."})

    await send_button_message(
        jid,
        formatted_text,
        [{"type": "list", "buttonText": button_label, "text": button_label, "sections": sections}],
        options,
        title=data.title or "",
        footer=data.footer or "",
    )
    return {"success": True, "message": "Option list sent."}
