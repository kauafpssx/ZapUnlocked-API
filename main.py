"""
ZapUnlocked-API — FastAPI + WhatsApp automation entry point.

This file is intentionally kept thin. All environment bootstrapping
lives in src/bootstrap.py; the application lifespan lives in src/lifespan.py.
"""

import os
import sys
from pathlib import Path

# Reduce memory arena usage on small servers
os.environ.setdefault("MALLOC_ARENA_MAX", "1")

# ── Auto-activate venv if present and not already inside it ──
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_VENV_DIR = os.path.join(_THIS_DIR, ".venv")
_VENV_PYTHON = os.path.join(_VENV_DIR, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(_VENV_DIR, "bin", "python")

if (
    os.path.isdir(_VENV_DIR)
    and os.path.isfile(_VENV_PYTHON)
    and not os.path.realpath(sys.executable).startswith(os.path.realpath(_VENV_DIR))
):
    os.execv(_VENV_PYTHON, [_VENV_PYTHON, __file__, *sys.argv[1:]])

# ── Environment bootstrap (libmagic, paths, dep validation) ──
from src.bootstrap import bootstrap

bootstrap()

# ── App creation and server launch ──
from src.lifespan import lifespan
from src.app import create_app
import uvicorn
from src.config.constants import PORT

app = create_app(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="::",
        port=PORT,
        proxy_headers=True,
        log_level="info",
    )
