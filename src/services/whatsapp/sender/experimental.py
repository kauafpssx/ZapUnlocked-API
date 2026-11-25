"""Experimental sender for WhatsApp native forms (galaxy_message)."""

from __future__ import annotations

import json
import os

from src.services.whatsapp.sender.native_flow import send_native_flow_message
from src.utils.logger import logger


def is_enabled() -> bool:
    return os.getenv("ENABLE_EXPERIMENTAL_NATIVE_FORMS", "false").lower() in ("1", "true", "yes")


async def send_form_message(
    jid: str,
    text: str = "",
    params=None,
    message_params=None,
    title: str = "",
    footer: str = "",
    version: int = 3,
    fallback_url: str = None,
    image_url: str = None,
    options: dict = None,
    session_id: str = "1",
    flow_id: str = None,
    flow_token: str = None,
    flow_cta: str = None,
    full_name_visible: bool = True,
    email_visible: bool = True,
    phone_number_visible: bool = False,
    delivery_address_visible: bool = False,
    custom_fields=None,
    **kwargs,
):
    if not is_enabled():
        raise RuntimeError("Experimental native forms are disabled.")

    if params is None:
        params = {}
    if isinstance(params, str):
        try:
            parsed = json.loads(params)
            params = parsed if isinstance(parsed, dict) else {"value": parsed}
        except (ValueError, TypeError):
            params = {"value": params}
    if not isinstance(params, dict):
        params = {"value": params}

    # Build the canonical galaxy_message payload when the caller did not pass
    # an explicit params dict. Based on the reverse-engineered Native Flow.
    if not params:
        flow_id = flow_id or "1367132928903753"
        flow_token = flow_token or "Q1VTVE9NRVJfSU5GTw=="
        flow_cta = flow_cta or "Complete form"
        data = {
            "full_name_visible": bool(full_name_visible),
            "email_visible": bool(email_visible),
            "phone_number_visible": bool(phone_number_visible),
            "delivery_address_visible": bool(delivery_address_visible),
            "custom_fields": custom_fields or [],
        }
        params = {
            "flow_id": flow_id,
            "flow_token": flow_token,
            "flow_cta": flow_cta,
            "flow_action": "navigate",
            "flow_message_version": "4",
            "form_type": "template",
            "flow_action_payload": {
                "screen": "contact_details",
                "data": data,
            },
        }

    if fallback_url:
        params.setdefault("fallback_url", fallback_url)

    button = {"name": "galaxy_message", "params": params}

    res = await send_native_flow_message(
        jid,
        text,
        buttons=[button],
        options=options,
        title=title,
        footer=footer,
        version=3,  # must be 3 for the form to render
        message_params=None,  # adding messageParamsJSON breaks rendering
        image_url=image_url,
        session_id=session_id,
        **kwargs,
    )
    # Attach flow_token for caller correlation when available.
    try:
        res._flow_token = params.get("flow_token")
    except Exception:
        pass
    logger.info(f"Experimental form payload: {json.dumps(params, ensure_ascii=False)}")
    logger.warning("Experimental native form sent; compatibility is not guaranteed.")
    return res