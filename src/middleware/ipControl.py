from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger
from src.services.whatsapp.settingsService import get_settings
import time

class IPControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Get real IP (considering proxies/load balancers if present)
        # FastAPI usually puts the IP in request.client.host
        client_ip = request.client.host
        
        # 2. Logger: Print IP of each request
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        logger.info(f"📥 Request: {method} {path} | IP: {client_ip}")

        # 3. Access Control (Blacklist/Whitelist)
        settings = get_settings()
        
        if settings.get("ip_control_enabled", False):
            whitelist = settings.get("ip_whitelist", [])
            blacklist = settings.get("ip_blacklist", [])
            
            # Priority: Blacklist -> Whitelist
            if client_ip in blacklist:
                logger.warning(f"🚫 IP blocked by Blacklist: {client_ip}")
                raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "Access denied: IP is blacklisted."})

            if whitelist and client_ip not in whitelist:
                logger.warning(f"🚫 IP denied (not in Whitelist): {client_ip}")
                raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "Access denied: IP is not whitelisted."})

        # 4. Process the request
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code
            logger.info(f"📤 Response: {status_code} | Time: {process_time:.2f}ms | IP: {client_ip}")
            
            return response
        except HTTPException as he:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=he.status_code, content=he.detail)
        except Exception as e:
            logger.error(f"❌ Error in IP middleware: {str(e)}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": "Failed to process IP control."})
