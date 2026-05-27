import sys
import asyncio

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
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
