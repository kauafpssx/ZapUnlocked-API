import asyncio
from datetime import datetime, timezone

from src.utils.logger import logger


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def dispatch_event(event_type: str, data: dict) -> None:
    """Fire event_type to all active subscribed webhooks."""
    try:
        from src.services.webhookRegistry import get_active_webhooks_for_event
        from src.services.webhookService import trigger_webhook

        webhooks = get_active_webhooks_for_event(event_type)
        if not webhooks:
            return

        default_payload = {
            "event": event_type,
            "timestamp": _utc_now(),
            "data": data,
        }

        context = {**data, "event": event_type}

        for wh in webhooks:
            asyncio.create_task(
                trigger_webhook(wh, context, default_payload=default_payload)
            )

        logger.debug(f"📡 Evento '{event_type}' despachado para {len(webhooks)} webhook(s)")
    except Exception as e:
        logger.error(f"Failed to dispatch event '{event_type}': {e}")
