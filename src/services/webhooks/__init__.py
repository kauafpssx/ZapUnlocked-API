"""Webhook management — registry, dispatching, and delivery."""

# Re-export public symbols so callers can do:
#   from src.services.webhooks import dispatch_event, get_active_webhooks_for_event, trigger_webhook
# or import from individual sub-modules directly.

from src.services.webhooks.registry import (
    ALL_EVENTS,
    list_webhooks,
    get_webhook,
    create_webhook,
    update_webhook,
    delete_webhook,
    toggle_webhook,
    get_active_webhooks_for_event,
)
from src.services.webhooks.dispatcher import dispatch_event
from src.services.webhooks.service import trigger_webhook
