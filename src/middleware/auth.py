"""API key authentication middleware."""

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, APIKeyQuery

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
api_key_query = APIKeyQuery(name="API_KEY", auto_error=False)


async def auth(
    header_key: str = Security(api_key_header),
    query_key: str = Security(api_key_query),
) -> bool:
    current_key = os.getenv("API_KEY")
    if current_key and (header_key == current_key or query_key == current_key):
        return True

    raise HTTPException(
        status_code=401,
        detail={
            "error": "UNAUTHORIZED",
            "message": "Invalid or missing API key. Send via x-api-key header (preferred) or ?API_KEY= query param."
        },
    )
