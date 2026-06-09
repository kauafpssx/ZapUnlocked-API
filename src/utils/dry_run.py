"""DRY_RUN mode — intercept sends and return fake response without calling WhatsApp."""

import os
from src.utils.time import now_ts


def is_dry_run() -> bool:
    return os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")


def dry_run_response(message: str = "Message sent.") -> dict:
    return {
        "success": True,
        "dryRun": True,
        "message": message,
        "messageId": None,
        "timestamp": now_ts(),
    }


def dry_run_media_response(message: str = "Media queued.") -> dict:
    return {
        "success": True,
        "dryRun": True,
        "message": message,
    }
