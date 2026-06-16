import asyncio
from datetime import datetime, timezone

from src.utils.logger import logger


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    except Exception as e:
        logger.error(f"Failed to dispatch event '{event_type}': {e}")
