"""
Public URL builder for QR dashboard and callbacks.

Extracted from event_handlers.py to separate deployment-specific
logic from event processing (Clean Architecture dependency rule).
"""

import os
import socket

from src.config.constants import PORT, API_KEY


def build_qr_url() -> str:
    """Build the public /qr dashboard URL based on environment."""
    public_url = os.getenv("PUBLIC_URL")
    if not public_url:
        user = os.getenv("USER", "")
        if user:
            public_url = f"http://services-{user}.alwaysdata.net:{PORT}"
        else:
            hostname = socket.gethostname()
            public_url = f"http://{hostname}:{PORT}"
    else:
        if ":" not in public_url.split("/")[-1]:
            public_url = f"{public_url}:{PORT}"
    qr_url = f"{public_url}/qr"
    if API_KEY:
        qr_url += f"?API_KEY={API_KEY}"
    return qr_url
