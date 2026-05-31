"""
Pairing Code Controller — link a device via phone number (no QR).

Delegates all business logic to pairing_service for testability.
Keeps only the HTTP-layer concerns (request schema, response format).
"""

from fastapi import HTTPException
from pydantic import BaseModel

from src.services.whatsapp.pairing_service import generate_pairing_code
from src.utils.logger import logger


class PairRequest(BaseModel):
    phone: str


async def pair_device(data: PairRequest):
    """Generate a pairing code to link WhatsApp via phone number."""
    try:
        code = await generate_pairing_code(data.phone)
        return {"success": True, "code": code}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [PAIR] Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": f"Failed to generate pairing code: {str(e)}",
            },
        )
