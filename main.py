import sys
import os
import asyncio

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
    msg_title="ATENCAO: Voce esta no Alwaysdata"
    msg_body="A porta 8300-8499 so fica acessivel atraves de um Service"
    msg_hint="Advanced > Services > Add a service  |  Command: bash scripts/run/run.sh  |  Bind :: (IPv6)"
    msg_docs="https://help.alwaysdata.com/en/services"
    try:
        import subprocess
        subprocess.run(
            ["gum", "style",
             "--foreground", "196",
             "--border-foreground", "196",
             "--border", "rounded",
             "--align", "center",
             "--width", "60",
             "--padding", "1 2",
             msg_title, msg_body, msg_hint, msg_docs],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print(f"\n{'='*60}\n  {msg_title}\n  {msg_body}\n  {msg_hint}\n  {msg_docs}\n{'='*60}\n", file=sys.stderr)
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
