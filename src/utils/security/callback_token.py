"""
HMAC-based callback token utilities for button interactions.

Creates and verifies time-limited (24h) signed tokens so WhatsApp
button presses can securely trigger webhooks.
"""

import hmac
import hashlib
import json
import base64
import time
from src.config.constants import INTERNAL_SECRET
from src.utils.logger import logger


def _get_secret() -> str:
    """Return INTERNAL_SECRET or raise if not configured."""
    if not INTERNAL_SECRET:
        logger.error(
            "INTERNAL_SECRET not configured! Button callbacks will not work. "
            "Set INTERNAL_SECRET in .env."
        )
        raise RuntimeError(
            "INTERNAL_SECRET is not set in .env. "
            "Button callbacks require this key for security."
        )
    return INTERNAL_SECRET


def create_callback_payload(webhook: dict) -> str:
    """Create a 24h-expiry HMAC-SHA256 token for button callbacks."""
    now = int(time.time())
    exp = now + (24 * 60 * 60)
    secret = _get_secret()

    payload = {
        "w": {
            "u": webhook.get("url"),
            "m": str(webhook.get("method", "POST")).upper(),
            "h": webhook.get("headers", {}),
            "b": webhook.get("body", {}),
        },
        "r": webhook.get("reaction"),
        "exp": exp,
    }

    json_str = json.dumps(payload, separators=(",", ":"))
    signature = hmac.new(secret.encode("utf-8"), json_str.encode("utf-8"), hashlib.sha256).hexdigest()

    final_payload = {"p": payload, "s": signature[:16]}
    final_json = json.dumps(final_payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(final_json.encode("utf-8")).decode("utf-8")


def verify_and_decode_payload(token: str) -> dict | None:
    """Verify and decode a callback token. Returns config dict or None if invalid/expired."""
    try:
        json_str = base64.urlsafe_b64decode(token).decode("utf-8")
        data = json.loads(json_str)
        payload = data.get("p")
        signature = data.get("s")

        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None

        secret = _get_secret()
        payload_str = json.dumps(payload, separators=(",", ":"))
        expected_sig = (
            hmac.new(
                secret.encode("utf-8"),
                payload_str.encode("utf-8"),
                hashlib.sha256,
            )
            .hexdigest()[:16]
        )

        if not hmac.compare_digest(signature, expected_sig):
            return None

        return {
            "url": payload["w"]["u"],
            "method": payload["w"]["m"],
            "headers": payload["w"]["h"],
            "body": payload["w"]["b"],
            "reaction": payload.get("r"),
        }
    except Exception:
        return None
