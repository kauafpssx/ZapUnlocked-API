"""
Public URL builder for QR dashboard and callbacks.

Extracted from event_handlers.py to separate deployment-specific
logic from event processing (Clean Architecture dependency rule).
"""

import os

from src.config.constants import PORT, API_KEY
from src.utils.startup_validator import is_alwaysdata


def build_qr_url() -> str:
    """Build the /qr dashboard URL for the current environment.

    ``PUBLIC_URL`` is treated as the complete externally reachable origin. When
    running locally, use the loopback address instead of the Windows hostname;
    a LAN address can still be selected explicitly through ``PUBLIC_URL``.
    """
    configured_url = (os.getenv("PUBLIC_URL") or "").strip()
    if configured_url:
        public_url = configured_url.rstrip("/")
    elif is_alwaysdata():
        account = os.getenv("ALWAYSDATA_ACCOUNT") or os.getenv("USER", "")
        public_url = f"http://services-{account}.alwaysdata.net:{PORT}"
    else:
        public_url = f"http://127.0.0.1:{PORT}"

    qr_url = f"{public_url}/qr"
    if API_KEY:
        qr_url += f"?API_KEY={API_KEY}"
    return qr_url
