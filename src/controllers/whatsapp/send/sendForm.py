import os
from fastapi import HTTPException, Request

from src.utils.phone import resolve_jid
from src.utils.decorators import handle_errors, get_session_id
from src.utils.quote import build_send_options
from src.utils.formatter import format_text
from src.utils.time import sent_response
from src.utils.dry_run import is_dry_run, dry_run_response
from src.services.whatsapp.sender.experimental import send_form_message, is_enabled
from src.schemas.experimental import SendFormRequest


@handle_errors("send experimental form")
async def send_form(data: SendFormRequest, request: Request):
    if not is_enabled():
        raise HTTPException(status_code=404, detail={"error": "EXPERIMENTAL_DISABLED", "message": "Experimental native forms are disabled."})

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

    params = data.params
    if params is None and data.components is not None:
        params = {"components": data.components}
    if params is None and data.message_params is not None:
        params = data.message_params

    flow_token = data.flow_token or "Q1VTVE9NRVJfSU5GTw=="

    message_text = format_text(data.body or data.text or data.message or "")

    if is_dry_run():
        return dry_run_response("Experimental form sent (dry run).")

    res = await send_form_message(
        jid,
        message_text,
        params=params,
        message_params=None,
        title=data.title or "",
        footer=data.footer or "",
        version=data.version,
        fallback_url=data.fallback_url,
        image_url=data.image,
        options=options,
        session_id=sid,
        flow_id=data.flow_id,
        flow_token=flow_token,
        flow_cta=data.flow_cta,
        full_name_visible=data.full_name_visible,
        email_visible=data.email_visible,
        phone_number_visible=data.phone_number_visible,
        delivery_address_visible=data.delivery_address_visible,
        custom_fields=data.custom_fields,
    )
    resp = sent_response(res, "Experimental form sent.")
    resp["flowToken"] = flow_token
    return resp