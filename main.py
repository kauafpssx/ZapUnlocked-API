import asyncio
import os
import sys

# Reduz uso de memória em servidores pequenos
os.environ.setdefault("MALLOC_ARENA_MAX", "1")

# Flags de teste
BYPASS_ALWAYSDATA_CHECK = os.getenv("BYPASS_ALWAYSDATA_CHECK", "0") == "1"
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "1") == "1"
ENABLE_FFMPEG_WARMUP = os.getenv("ENABLE_FFMPEG_WARMUP", "1") == "1"

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Vendor local usado no AlwaysData
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if os.path.isdir(_VENDOR_DIR):
    sys.path.insert(0, _VENDOR_DIR)

# .local_lib antigo
_LOCAL_LIB = os.path.join(_THIS_DIR, ".local_lib")
if os.path.isdir(_LOCAL_LIB):
    sys.path.insert(0, _LOCAL_LIB)

# Auto-venv apenas se existir
_VENV_DIR = os.path.join(_THIS_DIR, ".venv")
if __name__ == "__main__":
    VENV_PYTHON = os.path.join(_VENV_DIR, "bin", "python")
    if sys.platform == "win32":
        VENV_PYTHON = os.path.join(_VENV_DIR, "Scripts", "python.exe")

    if (
        os.path.isdir(_VENV_DIR)
        and os.path.isfile(VENV_PYTHON)
        and not os.path.realpath(sys.executable).startswith(os.path.realpath(_VENV_DIR))
    ):
        os.execv(VENV_PYTHON, [VENV_PYTHON, __file__, *sys.argv[1:]])

from src.utils.startup_validator import is_alwaysdata, validate_dependencies

validate_dependencies()

if is_alwaysdata() and sys.stdin.isatty() and not BYPASS_ALWAYSDATA_CHECK:
    msg = (
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        "║   ATENCAO: Alwaysdata detectado                  ║\n"
        "║   A porta 8300-8499 so fica acessivel           ║\n"
        "║   apos registrar um Service no painel:           ║\n"
        "║     Advanced > Services > Add a service          ║\n"
        "║                                                  ║\n"
        "║   Name          ZapUnlocked-API                  ║\n"
        "║   Command       python3 main.py                  ║\n"
        "║   Working dir   ZapUnlocked-API                  ║\n"
        "║   Env vars      PORT=8300                        ║\n"
        "║                                                  ║\n"
        "║   Para testar manualmente:                       ║\n"
        "║   BYPASS_ALWAYSDATA_CHECK=1 python3 main.py      ║\n"
        "╚══════════════════════════════════════════════════╝\n"
    )

    try:
        import subprocess

        subprocess.run(
            [
                "gum",
                "style",
                "--foreground",
                "196",
                "--border-foreground",
                "196",
                "--border",
                "rounded",
                "--align",
                "center",
                "--width",
                "58",
                "--padding",
                "1 1",
                "ATENCAO: Alwaysdata detectado",
                "A porta 8300-8499 so fica acessivel",
                "apos registrar um Service no painel:",
                "Advanced > Services > Add a service",
                "",
                "Name......... ZapUnlocked-API",
                "Command...... python3 main.py",
                "Working dir.. ZapUnlocked-API",
                "Env vars..... PORT=8300",
                "",
                "Teste manual:",
                "BYPASS_ALWAYSDATA_CHECK=1 python3 main.py",
            ],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print(msg, file=sys.stderr)

    sys.exit(1)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger

from src.app import create_app
from src.config.constants import PORT


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENABLE_FFMPEG_WARMUP:
        try:
            from src.services.media.utils import warm_up_ffmpeg

            warm_up_ffmpeg()
        except Exception as e:
            logger.warning(f"FFmpeg warmup ignorado: {e}")

    if ENABLE_WHATSAPP:
        try:
            from src.services.whatsapp.client import start_bot

            asyncio.create_task(start_bot())
            logger.info("WhatsApp bot iniciado")
        except Exception as e:
            logger.error(f"Falha ao iniciar WhatsApp bot: {e}")
    else:
        logger.warning("WhatsApp bot desativado por ENABLE_WHATSAPP=0")

    logger.info(f"🚀 API rodando na porta {PORT}")
    yield


app = create_app(lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="::",
        port=PORT,
        proxy_headers=True,
        log_level="info",
    )
