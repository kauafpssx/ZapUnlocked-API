"""
Middleware that strips JSON comments and trailing commas before FastAPI parses the body.

Allows // and /* */ comments in JSON request bodies (useful for Postman inline docs).
"""

from fastapi import Request
from loguru import logger
from src.utils.parsing.json_cleaner import clean_json_text


async def json_comment_stripper(request: Request, call_next):
    """Strip JSON comments and trailing commas before FastAPI parses the body."""
    if request.method in ("POST", "PUT", "PATCH") \
       and "application/json" in request.headers.get("content-type", ""):
        body = await request.body()
        if body:
            try:
                text = body.decode("utf-8")
                cleaned_text = clean_json_text(text)
                if cleaned_text != text:
                    request._body = cleaned_text.encode("utf-8")
            except Exception as e:
                logger.debug(f"⚠️ Failed to clean JSON body: {e}")

    return await call_next(request)
