import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from loguru import logger
from typing import Any

from src.routes.index import router as root_router
from src.routes.send import router as send_router
from src.routes.qr import router as qr_router
from src.routes.management import router as management_router
from src.routes.settings import router as settings_router
from src.routes.contacts import router as contacts_router
from src.routes.system import router as system_router
from src.routes.instance import router as instance_router
from src.routes.webhooks import router as webhooks_router
from src.routes.session import router as session_router
from src.routes.ai import router as ai_router
from src.routes.sessions_mgmt import router as sessions_mgmt_router
from src.middleware.ip_control import IPControlMiddleware
from src.middleware.json_cleaner import json_comment_stripper


def create_app(lifespan: Any = None) -> FastAPI:

    app = FastAPI(title="ZapUnlocked API", version="1.5.2", lifespan=lifespan)

    # Middlewares — IP control runs first for logging + access control
    app.add_middleware(IPControlMiddleware)

    # CORS — read allowed origins from env (comma-separated), fall back to "*"
    cors_origins_env = os.getenv("CORS_ORIGINS", "*")
    cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "x-api-key"],
    )

    # JSON comment stripping middleware (allows // and /* */ in request bodies)
    app.middleware("http")(json_comment_stripper)

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

    # ── Static files (images, etc) ────────────────────────────
    _static_dir = Path(__file__).resolve().parent / "static"
    if _static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

    # ── Temp media (Meta AI images, etc) — only when META_AI_KEEP_IMAGES=true ──
    from src.config.constants import TEMP_DIR, IS_ALWAYSDATA
    if os.getenv("META_AI_KEEP_IMAGES", "false").lower() == "true" and not IS_ALWAYSDATA:
        Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
        app.mount("/media", StaticFiles(directory=TEMP_DIR), name="media")

    # ── Favicon ──────────────────────────────────────────────
    _favicon_path = Path(__file__).resolve().parent.parent / "favicon.ico"
    if _favicon_path.exists():

        @app.get("/favicon.ico", include_in_schema=False)
        async def favicon():
            return FileResponse(str(_favicon_path), media_type="image/x-icon")

    # Routes
    app.include_router(root_router)
    app.include_router(system_router, prefix="/system")
    app.include_router(send_router)
    app.include_router(qr_router, prefix="/qr")
    app.include_router(management_router, prefix="/management")
    app.include_router(settings_router, prefix="/settings")
    app.include_router(contacts_router, prefix="/contacts")
    app.include_router(instance_router, prefix="/instance")
    app.include_router(webhooks_router, prefix="/webhooks")
    app.include_router(session_router, prefix="/session")
    app.include_router(ai_router, prefix="/ai")
    app.include_router(sessions_mgmt_router)

    return app
