"""
Pairing service — generates WhatsApp pairing codes via phone number.

Encapsulates the PairPhone() call logic that was previously inline
in pairController.py, making it testable and reusable.
"""

import asyncio
import re
from fastapi import HTTPException

from src.services.whatsapp.state import get_client, get_is_ready
from src.utils.logger import logger


async def generate_pairing_code(phone: str, timeout: float = 75.0) -> str:
    """Generate a WhatsApp pairing code for the given phone number.

    Args:
        phone: Phone number with country code (e.g. 5511999999999).
        timeout: Maximum seconds to wait for the pairing code.

    Returns:
        The pairing code string.

    Raises:
        HTTPException: With appropriate status code for each failure mode.
    """
    if get_is_ready():
        raise HTTPException(
            status_code=409,
            detail={
                "error": "WHATSAPP_ALREADY_CONNECTED",
                "message": "WhatsApp is already connected. Disconnect before pairing again.",
            },
        )

    sock = get_client()
    if not sock:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SERVICE_UNAVAILABLE",
                "message": "WhatsApp service is not initialized.",
            },
        )

    clean_phone = _sanitize_phone(phone)
    if not clean_phone:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "MISSING_FIELD",
                "message": "Phone number is required (e.g. 5511999999999).",
            },
        )

    logger.info(f"🔗 [PAIR] Requesting pairing code for: {clean_phone}")

    try:
        code = await asyncio.wait_for(
            asyncio.to_thread(
                sock.PairPhone,
                clean_phone,
                True,  # show_push_notification
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error(f"❌ [PAIR] Timed out ({timeout}s limit)")
        raise HTTPException(
            status_code=408,
            detail={
                "error": "TIMEOUT",
                "message": (
                    f"Timed out waiting for pairing code. The phone number may be "
                    f"invalid, not registered on WhatsApp, or rate-limited. "
                    f"Verify the format (e.g. 5511999999999 for Brazil)."
                ),
            },
        )

    if not code or not isinstance(code, str):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PAIR_FAILED",
                "message": (
                    "Pairing code was not generated. Check that the phone number "
                    "is correctly formatted (e.g. 5551988887777)."
                ),
            },
        )

    logger.info(f"✅ Pairing code generated for {clean_phone}: {code}")
    return code


def _sanitize_phone(phone: str) -> str:
    """Remove all non-digit characters from a phone number."""
    return re.sub(r"[^0-9]", "", phone)
