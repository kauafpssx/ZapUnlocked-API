from src.utils.phone import resolve_jid
from fastapi import HTTPException, Request
from src.services.whatsapp.sender.native_flow import send_native_flow_message
from src.utils.decorators import require_whatsapp, handle_errors, get_session_id
from src.utils.logger import logger
from src.utils.quote import build_send_options
from src.utils.formatter import format_text
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.schemas.interactive import SendNativeFlowRequest


@require_whatsapp
@handle_errors("send native flow")
async def send_native_flow(data: SendNativeFlowRequest, request: Request):
    sid = get_session_id(request)
    jid = resolve_jid(data.phone)

    options = await build_send_options(
        jid,
        reply_identifier=data.quoted_id,
        reply_type=data.type or "id",
        delay_message=data.delay_message,
        delay_typing=data.delay_typing,
        mentioned=data.mentioned,
    )

    message_text = format_text(data.resolved_text())
    buttons_to_send = []
    for btn in data.resolved_buttons():
        if hasattr(btn, "model_dump"):
            btn = btn.model_dump(by_alias=True)
        name = btn.get("name", btn.get("type", "quick_reply"))
        params = btn.get("params", None)
        entry = {"name": name}
        if btn.get("buttonParamsJSON") is not None:
            entry["buttonParamsJSON"] = btn.get("buttonParamsJSON")
        if params is not None:
            entry["params"] = params
        buttons_to_send.append(entry)

    if not buttons_to_send and data.serialized_message_params() is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "MISSING_FIELD", "message": "At least one button or messageParams must be provided."},
        )

    if is_dry_run():
        return dry_run_response("Native flow message sent.")
    res = await send_native_flow_message(
        jid,
        message_text,
        buttons=buttons_to_send,
        options=options,
        title=data.title or "",
        footer=data.footer or "",
        version=data.version,
        message_params=data.message_params,
        message_params_json=data.message_params_json,
        image_url=data.image,
        session_id=sid,
    )
    return sent_response(res, "Native flow message sent.")