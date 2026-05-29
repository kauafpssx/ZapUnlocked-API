import sys
import os
import asyncio

# ── Auto-venv: reexecuta com o Python do .venv se chamado diretamente ──────
if __name__ == "__main__":
    VENV_PYTHON = os.path.join(os.path.dirname(__file__), ".venv", "bin", "python")
    if sys.platform == "win32":
        VENV_PYTHON = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
    if not sys.executable.startswith(os.path.join(os.path.dirname(__file__), ".venv")):
        if os.path.isfile(VENV_PYTHON):
            os.execv(VENV_PYTHON, [VENV_PYTHON, __file__, *sys.argv[1:]])

from src.utils.startup_validator import validate_dependencies
validate_dependencies()

# FIX: Configura o ProactorEventLoop como global para suporte a subprocessos no Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn
from loguru import logger
from src.app import create_app
from src.config.constants import PORT
from src.services.whatsapp.client import start_bot
from src.services.media.utils import warm_up_ffmpeg
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    warm_up_ffmpeg()
    asyncio.create_task(start_bot())
    logger.info(f"🚀 API rodando na porta {PORT}")
    yield

app = create_app(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run("main:app", host="::", port=PORT, proxy_headers=True, log_level="info")
