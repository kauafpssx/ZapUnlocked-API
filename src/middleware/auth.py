"""API key authentication middleware."""

import os

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader, APIKeyQuery

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
api_key_query = APIKeyQuery(name="API_KEY", auto_error=False)


async def auth(
    request: Request,
    header_key: str = Security(api_key_header),
    query_key: str = Security(api_key_query),
) -> bool:
    current_key = os.getenv("API_KEY")
    if current_key and (header_key == current_key or query_key == current_key):
        # Resolve session_id from X-Instance header or ?session= query param
        from src.services.sessions.registry import get_default_session_id
        session_id = (
            request.headers.get("X-Instance")
            or request.query_params.get("session")
            or get_default_session_id()
        )
        request.state.session_id = session_id
        return True

    raise HTTPException(
        status_code=401,
        detail={
            "error": "UNAUTHORIZED",
            "message": "Invalid or missing API key. Send via x-api-key header (preferred) or ?API_KEY= query param."
        },
    )
