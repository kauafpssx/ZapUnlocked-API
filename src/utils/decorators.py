"""
Reusable FastAPI decorators for controller boilerplate.

Usage:
    @require_whatsapp
    @handle_errors("send message")
    async def my_handler(data: RequestSchema):
        ...  # clean logic, no try/except
"""

import functools
from fastapi import HTTPException


def require_whatsapp(fn):
    """Raise 503 immediately if WhatsApp is not connected."""
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        from src.services.whatsapp.client import get_is_ready
        if not get_is_ready():
            raise HTTPException(
                status_code=503,
                detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."},
            )
        return await fn(*args, **kwargs)
    return wrapper


def handle_errors(action_name: str = "perform operation"):
    """
    Decorator that wraps an async controller function in try/except,
    logs the error with a descriptive action name, and returns a
    standardised 500 response.

    Re-raise :class:`HTTPException` as-is so that status-code-specific
    errors (400, 404, etc.) are not swallowed.
    """
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                from src.utils.logger import logger
                logger.error(f"❌ Failed to {action_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail={"error": "INTERNAL_ERROR", "message": str(e)},
                )
        return wrapper
    return decorator
