"""IP-based access control middleware."""

import time

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.ip_rules_service import is_ip_blocked, is_ip_allowed, get_ip_rules
from src.services.whatsapp.settingsService import get_settings
from src.utils.logger import logger


def extract_client_ip(request: Request) -> str:
    """
    Extract the real client IP address from the request.

    Priority:
      1. X-Forwarded-For header (set by proxies / load balancers)
      2. X-Real-IP header
      3. request.client.host (direct connection)
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown"


class IPControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = extract_client_ip(request)
        start_time = time.time()
        method = request.method
        path = request.url.path

        via = ""
        if request.headers.get("X-Forwarded-For"):
            via = " (via proxy)"
        elif request.headers.get("X-Real-IP"):
            via = " (via X-Real-IP)"

        logger.info(f"📥 {method} {path} | Origin: {client_ip}{via}")

        settings = get_settings()
        if settings.get("ip_control_enabled", False):
            self._check_access(client_ip)

        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"📤 {response.status_code} | {process_time:.2f}ms | Origin: {client_ip}")
        return response

    def _check_access(self, client_ip: str) -> None:
        """Enforce whitelist/blacklist for the given IP."""
        if is_ip_blocked(client_ip):
            logger.warning(f"🚫 Blocked by blacklist: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail={"error": "FORBIDDEN", "message": "Access denied: IP is blacklisted.", "ip": client_ip},
            )
        allowed = is_ip_allowed(client_ip)
        if allowed is None:
            logger.warning(f"🚫 Blocked by blacklist: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail={"error": "FORBIDDEN", "message": "Access denied: IP is blacklisted.", "ip": client_ip},
            )
        if allowed is False:
            logger.warning(f"🚫 Denied (not in whitelist): {client_ip}")
            raise HTTPException(
                status_code=403,
                detail={"error": "FORBIDDEN", "message": "Access denied: IP is not whitelisted.", "ip": client_ip},
            )
