"""
Main message handler — entrance point for incoming WhatsApp messages.

Detects embedded button callbacks (cb=), optionally reacts, fires
webhooks, and falls through to structured event dispatch.
"""

import asyncio

from src.utils.parsing.message_parser import parse_message, should_ignore_message
from src.utils.security.callback_token import verify_and_decode_payload
from src.services.webhooks.service import trigger_webhook
from src.handlers.message_router import dispatch_message_event
from src.utils.logger import logger


async def handleMessage(client, msg):
    """
    Main handler: detects embedded callbacks (cb=) and dispatches webhook events
    for all incoming message types.
    """
    if should_ignore_message(msg):
        return

    parsed = parse_message(msg)
    if not parsed:
        return

    phone = parsed["phone"]
    text = parsed["text"] or ""
    button_response = parsed["buttonResponse"] or ""

    # ── BUTTON CALLBACK (cb=) ─────────────────────────────
    callback_part = None
    if isinstance(button_response, str) and button_response.startswith("cb="):
        callback_part = button_response[3:]
    elif "|cb=" in text:
        callback_part = text.split("|cb=")[1]

    if callback_part:
        webhook_config = verify_and_decode_payload(callback_part)
        if webhook_config:
            button_label = text or "Button clicked"
            logger.info(f'🎯 Callback detected: "{button_label}" from {phone}')

            if webhook_config.get("reaction"):
                try:
                    from src.services.whatsapp.sender import send_reaction
                    await send_reaction(phone, msg.Info.ID, webhook_config["reaction"])
                    logger.info(f"💖 Reacted with {webhook_config['reaction']} for {phone}")
                except Exception as err:
                    logger.error(f"Failed to react to message: {str(err)}")

            if webhook_config.get("url"):
                try:
                    asyncio.create_task(trigger_webhook(webhook_config, {
                        "from": phone,
                        "text": button_label,
                    }))
                except Exception as err:
                    logger.error(f"Failed to fire callback webhook: {str(err)}")
        elif isinstance(button_response, str) and button_response.startswith("cb="):
            logger.warning(f"⚠️ Invalid or expired callback received from {phone}")
        return

    # ── DISPATCH WEBHOOK EVENTS ──────────────────
    asyncio.create_task(dispatch_message_event(msg, phone, parsed))
