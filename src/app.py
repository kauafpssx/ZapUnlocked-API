import sys
import asyncio

# Force ProactorEventLoopPolicy before anything else
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
    """Strip // and /* */ comments and trailing commas from JSON text."""
    # Remove // comments (unless preceded by : to avoid breaking URLs)
    text = re.sub(r'(?<!:)\s*//.*', '', text)
    # Remove /* */ comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Remove trailing commas before } or ]
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
        """Strip JSON comments and trailing commas before FastAPI parses the body.

        Allows // and /* */ comments in request bodies (useful for Postman inline docs).
        """
        if request.method in ("POST", "PUT", "PATCH") \
           and "application/json" in request.headers.get("content-type", ""):
            body = await request.body()
            if body:
                try:
                    text = body.decode("utf-8")
                    cleaned_text = clean_json_text(text)
                    if cleaned_text != text:
                        # Overwrite FastAPI's internal body cache so it parses the cleaned version.
                        request._body = cleaned_text.encode("utf-8")
                except Exception as e:
                    logger.debug(f"⚠️ Failed to clean JSON body: {e}")
        
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"⚠️ Malformed payload received: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request body contains a validation error. Check field types and required fields.",
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
