from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger
from src.services.whatsapp.settingsService import get_settings
import time

class IPControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Obter o IP real (considerando proxies/load balancers se existirem)
        # O FastAPI geralmente coloca o IP em request.client.host
        client_ip = request.client.host
        
        # 2. Logger: Printar IP de cada request
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        logger.info(f"📥 Request: {method} {path} | IP: {client_ip}")

        # 3. Access Control (Blacklist/Whitelist)
        settings = get_settings()
        
        if settings.get("ip_control_enabled", False):
            whitelist = settings.get("ip_whitelist", [])
            blacklist = settings.get("ip_blacklist", [])
            
            # Prioridade: Blacklist -> Whitelist
            if client_ip in blacklist:
                logger.warning(f"🚫 IP bloqueado pela Blacklist: {client_ip}")
                raise HTTPException(status_code=403, detail="Acesso negado: IP na lista negra.")
            
            if whitelist and client_ip not in whitelist:
                logger.warning(f"🚫 IP negado (Não está na Whitelist): {client_ip}")
                raise HTTPException(status_code=403, detail="Acesso negado: Seu IP não possui permissão.")

        # 4. Processar a request
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            status_code = response.status_code
            logger.info(f"📤 Response: {status_code} | Tempo: {process_time:.2f}ms | IP: {client_ip}")
            
            return response
        except HTTPException as he:
            # Re-raise HTTP exceptions from middleware
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=he.status_code, content={"error": "Access Denied", "detail": he.detail})
        except Exception as e:
            logger.error(f"❌ Erro no middleware de IP: {str(e)}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"error": "Internal Server Error", "detail": "Erro ao processar controle de IP."})
