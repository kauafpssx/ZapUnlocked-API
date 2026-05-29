import asyncio
import os
import sys
from pathlib import Path

# Reduce memory arena usage on small servers
os.environ.setdefault("MALLOC_ARENA_MAX", "1")

# Windows: python-magic-bin bundles libmagic.dll under magic/libmagic/ but
# python-magic's loader only searches PATH and ./. Prepend the directory so
# ctypes.util.find_library and LoadLibrary can resolve it.
if sys.platform == "win32":
    _libmagic_dir = Path(sys.executable).parent.parent / "Lib" / "site-packages" / "magic" / "libmagic"
    if _libmagic_dir.exists():
        os.environ["PATH"] = str(_libmagic_dir) + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(str(_libmagic_dir))

ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "1") == "1"
ENABLE_FFMPEG_WARMUP = os.getenv("ENABLE_FFMPEG_WARMUP", "1") == "1"

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Legacy .local_lib (lowest priority)
_LOCAL_LIB = os.path.join(_THIS_DIR, ".local_lib")
if os.path.isdir(_LOCAL_LIB):
    sys.path.insert(0, _LOCAL_LIB)

# vendor takes highest priority (inserted last = sys.path[0])
_VENDOR_DIR = os.path.join(_THIS_DIR, "vendor")
if os.path.isdir(_VENDOR_DIR):
    sys.path.insert(0, _VENDOR_DIR)

# Auto-activate venv if present and not already inside it
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

if is_alwaysdata() and sys.stdin.isatty():
    msg = (
        "\n"
        "╔══════════════════════════════════════════════════════╗\n"
        "║  ⚠  ALWAYSDATA — SERVICE REQUIRED                   ║\n"
        "╠══════════════════════════════════════════════════════╣\n"
        "║                                                      ║\n"
        "║  Port 8300-8499 is only accessible after             ║\n"
        "║  registering this app as a Service in the panel.     ║\n"
        "║                                                      ║\n"
        "║  Advanced › Services › Add a service                 ║\n"
        "║                                                      ║\n"
        "╠══════════════════════════════════════════════════════╣\n"
        "║  Field           Value                               ║\n"
        "║  ─────────────   ─────────────────────────────────   ║\n"
        "║  Name            ZapUnlocked-API                     ║\n"
        "║  Command         bash scripts/run/run.sh             ║\n"
        "║  Working dir     ZapUnlocked-API                     ║\n"
        "║  Env vars        PORT=8300                           ║\n"
        "║                                                      ║\n"
        "╚══════════════════════════════════════════════════════╝\n"
    )

    try:
        import subprocess

        subprocess.run(
            [
                "gum",
                "style",
                "--foreground", "214",
                "--border-foreground", "214",
                "--border", "rounded",
                "--align", "left",
                "--width", "58",
                "--padding", "1 2",
                "⚠  ALWAYSDATA — SERVICE REQUIRED\n",
                "Port 8300-8499 is only accessible after",
                "registering this app as a Service in the panel.\n",
                "Advanced › Services › Add a service\n",
                "──────────────────────────────────────────────",
                "Field           Value",
                "─────────────   ─────────────────────────────",
                "Name            ZapUnlocked-API",
                "Command         bash scripts/run/run.sh",
                "Working dir     ZapUnlocked-API",
                "Env vars        PORT=8300",
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
            logger.warning(f"FFmpeg warmup skipped: {e}")

    if ENABLE_WHATSAPP:
        try:
            from src.services.whatsapp.client import start_bot

            asyncio.create_task(start_bot())
            logger.info("WhatsApp bot started")
        except Exception as e:
            logger.error(f"Failed to start WhatsApp bot: {e}")
    else:
        logger.warning("WhatsApp bot disabled (ENABLE_WHATSAPP=0)")

    logger.info(f"🚀 API running on port {PORT}")
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
