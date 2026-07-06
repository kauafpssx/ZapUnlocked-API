import asyncio
from datetime import datetime, timezone

from src.utils.logger import logger


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_SELF_DESTRUCT_EVENTS = {
    "message.audio",
    "message.image",
    "message.video",
    "message.document",
    "message.sticker",
    "message.text",
}


async def dispatch_event(event_type: str, data: dict, session_id: str = "1") -> None:
    """Fire event_type to all active subscribed webhooks for the given session."""
    try:
        from src.services.webhooks.registry import get_active_webhooks_for_event
        from src.services.webhooks.service import trigger_webhook

        webhooks = get_active_webhooks_for_event(event_type, session_id)
        if not webhooks:
            return

        default_payload = {
            "event": event_type,
            "timestamp": _utc_now(),
            "data": data,
        }

        context = {**data, "event": event_type}

        from src.services.stats import increment, increment_webhook
        for wh in webhooks:
            asyncio.create_task(
                trigger_webhook(wh, context, default_payload=default_payload, _event=event_type, session_id=session_id)
            )
            increment_webhook(wh.get("name", "unknown"), session_id=session_id)

        increment("webhooks_fired", len(webhooks), session_id=session_id)
        logger.debug(f"📡 Event '{event_type}' dispatched to {len(webhooks)} webhook(s) (session={session_id})")

        has_self_destruct = any(
            wh.get("self_destruct") for wh in webhooks
        )
        if has_self_destruct and event_type in _SELF_DESTRUCT_EVENTS:
            asyncio.create_task(_self_destruct_message(event_type, data, session_id))

    except Exception as e:
        logger.error(f"Failed to dispatch event '{event_type}': {e}")


async def _self_destruct_message(event_type: str, data: dict, session_id: str = "1"):
    """Delete message from WhatsApp after webhook dispatch."""
    message_id = data.get("messageId")
    jid = data.get("fromJid") or data.get("from")
    if not message_id or not jid:
        logger.warning(f"[SelfDestruct] missing messageId or JID — skipping")
        return

    try:
        from src.utils.phone import resolve_jid
        from src.services.whatsapp.sender import delete_message

        target_jid = resolve_jid(jid)
        await delete_message(target_jid, message_id, is_from_me=True, session_id=session_id)
        logger.info(f"💥 Self-destructed {event_type} ({message_id}) in {target_jid}")
    except Exception as e:
        logger.warning(f"[SelfDestruct] failed for {event_type} {message_id}: {e}")
