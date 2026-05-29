import sys
import os
import asyncio

# ── Garante que user site-packages esteja no path (Alwaysdata) ──────────────
import site as _site
try:
    _site.addsitedir(_site.getusersitepackages())
except Exception:
    pass

# ── Auto-venv: reexecuta com o Python do .venv se chamado diretamente ──────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_DIR = os.path.join(_THIS_DIR, ".venv")
if __name__ == "__main__":
    VENV_PYTHON = os.path.join(_VENV_DIR, "bin", "python")
    if sys.platform == "win32":
        VENV_PYTHON = os.path.join(_VENV_DIR, "Scripts", "python.exe")
    if not os.path.realpath(sys.executable).startswith(os.path.realpath(_VENV_DIR)):
        if os.path.isfile(VENV_PYTHON):
            os.execv(VENV_PYTHON, [VENV_PYTHON, __file__, *sys.argv[1:]])

from src.utils.startup_validator import validate_dependencies, is_alwaysdata
validate_dependencies()

# ── No Alwaysdata, a porta 8300-8499 so fica acessivel via Service ─────
if is_alwaysdata() and sys.stdin.isatty():
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
        "║   Veja: README.md secao Alwaysdata               ║\n"
        "╚══════════════════════════════════════════════════╝\n"
    )
    try:
        import subprocess
        subprocess.run(
            ["gum", "style",
             "--foreground", "196",
             "--border-foreground", "196",
             "--border", "rounded",
             "--align", "center",
             "--width", "56",
             "--padding", "1 1",
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
             "Veja: README.md secao Alwaysdata"],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print(msg, file=sys.stderr)
    sys.exit(1)

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
