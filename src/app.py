import sys
import asyncio

# Força o ProactorEventLoopPolicy antes de qualquer outra coisa
if sys.platform == "win32":
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
import re
import json

from src.routes.index import router as root_router
from src.routes.send import router as send_router
from src.routes.qr import router as qr_router
from src.routes.management import router as management_router
from src.routes.settings import router as settings_router
from src.routes.contacts import router as contacts_router
from src.routes.system import router as system_router
from src.routes.instance import router as instance_router
from src.routes.webhooks import router as webhooks_router
from src.middleware.ipControl import IPControlMiddleware
from typing import Any

def clean_json_text(text: str) -> str:
    """Remove comentários (// ou /* */) e evita erros com vírgulas extras no final."""
    # Remover comentários // (desde que não sejam precedidos por : para não quebrar URLs)
    text = re.sub(r'(?<!:)\s*//.*', '', text)
    # Remover comentários /* */
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remover vírgulas residuais antes de fechar } ou ]
    text = re.sub(r',\s*([\]}])', r'\1', text)
    return text.strip()

def create_app(lifespan: Any = None) -> FastAPI:
    
    app = FastAPI(title="ZapUnlocked API", version="1.5.2", lifespan=lifespan)

    # Middlewares
    app.add_middleware(IPControlMiddleware) # Logging e Controle de IP vem primeiro
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "x-api-key"],
    )

    @app.middleware("http")
    async def json_comment_stripper(request: Request, call_next):
        """Middleware para limpar comentários e vírgulas extras do JSON antes de processar.
        
        Remove comentários // e /* */ e vírgulas residuais do JSON enviado no body.
        O Postman não suporta comentários em JSON, mas este middleware permite usá-los
        como documentação inline dos campos.
        """
        if request.method in ("POST", "PUT", "PATCH") \
           and "application/json" in request.headers.get("content-type", ""):
            body = await request.body()
            if body:
                try:
                    text = body.decode("utf-8")
                    cleaned_text = clean_json_text(text)
                    if cleaned_text != text:
                        # Sobrescreve o cache interno do body para que o FastAPI
                        # use a versão limpa ao fazer o parsing do JSON.
                        request._body = cleaned_text.encode("utf-8")
                except Exception as e:
                    logger.debug(f"⚠️ Falha ao tentar limpar JSON: {e}")
        
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"⚠️ Payload malformado recebido: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "JSON malformado ou dados inválidos",
                "message": "O corpo da requisição contém um erro de validação. Verifique os tipos e campos enviados.",
                "details": exc.errors()
            }
        )

    # Rotas
    app.include_router(root_router)
    app.include_router(system_router, prefix="/system")
    app.include_router(send_router)
    app.include_router(qr_router, prefix="/qr")
    app.include_router(management_router, prefix="/management")
    app.include_router(settings_router, prefix="/settings")
    app.include_router(contacts_router, prefix="/contacts")
    app.include_router(instance_router, prefix="/instance")
    app.include_router(webhooks_router, prefix="/webhooks")

    return app
