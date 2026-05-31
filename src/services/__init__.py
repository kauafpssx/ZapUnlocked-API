"""Application services (business logic, external integrations)."""

# Re-export webhooks as webhookRegistry so controllers can do:
#   from src.services import webhookRegistry
#   webhookRegistry.list_webhooks()
from . import webhooks as webhookRegistry
