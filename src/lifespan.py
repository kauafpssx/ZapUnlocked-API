"""
FastAPI lifespan — application startup and shutdown lifecycle.

Owns directory creation, FFmpeg warmup, and WhatsApp bot initialisation.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from loguru import logger

from src.config.constants import PORT, AUTH_DIR, DATA_DIR, TEMP_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup tasks before yielding, shutdown after."""
    # ── Ensure required directories ─────────────────────────
    _ensure_dirs()

    # ── Initialise SQLite schema ─────────────────────────────
    _init_db()

    # ── FFmpeg warmup ───────────────────────────────────────
    _warm_up_ffmpeg()

    # ── WhatsApp bot(s) ─────────────────────────────────────
    await _start_whatsapp()

    # ── Media auto-cleanup loop ─────────────────────────
    asyncio.create_task(_media_cleanup_loop())

    # ── Log compression + cleanup loop ──────────────────
    asyncio.create_task(_logs_cleanup_loop())

    logger.info(f"🚀 API running on port {PORT}")
    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 Shutting down — disconnecting WhatsApp...")
    await _stop_whatsapp()


# ── Internal helpers ────────────────────────────────────────


def _ensure_dirs():
    """Create data directories if they don't exist."""
    Path(AUTH_DIR).mkdir(parents=True, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Auth directory: {AUTH_DIR}")
    logger.info(f"📁 Data directory: {DATA_DIR}")


def _init_db():
    try:
        from src.utils.db import init_db
        init_db()
        logger.info("🗄️ SQLite schema ready.")
    except Exception as e:
        logger.error(f"Failed to initialise database: {e}")
        raise


def _warm_up_ffmpeg():
    """Pre-warm FFmpeg if enabled."""
    enable = os.getenv("ENABLE_FFMPEG_WARMUP", "1") == "1"
    if not enable:
        logger.info("FFmpeg warmup disabled (ENABLE_FFMPEG_WARMUP=0)")
        return

    try:
        from src.services.media.utils import warm_up_ffmpeg
        warm_up_ffmpeg()
    except Exception as e:
        logger.warning(f"FFmpeg warmup skipped: {e}")


async def _start_whatsapp():
    """Start WhatsApp bot for all active sessions."""
    enable = os.getenv("ENABLE_WHATSAPP", "1") == "1"
    if not enable:
        logger.warning("WhatsApp bot disabled (ENABLE_WHATSAPP=0)")
        return

    try:
        from src.services.whatsapp.client import start_bot
        from src.services.whatsapp import state as _wa_state
        from src.services.sessions.registry import get_active_sessions, ensure_default_session
        ensure_default_session()
        sessions = get_active_sessions()
        for session in sessions:
            sid = session["id"]
            # Allow QR to be stored when WhatsApp emits it during startup
            _wa_state.set_keep_qr_active_on_restart(True, sid)
            asyncio.create_task(start_bot(sid))
            logger.info(f"WhatsApp bot started for session '{sid}' ({session.get('name', sid)})")
    except Exception as e:
        logger.error(f"Failed to start WhatsApp bot: {e}")


async def _stop_whatsapp():
    """Gracefully disconnect all neonize clients on shutdown, then force-exit."""
    try:
        from src.services.whatsapp import state
        from src.services.whatsapp.client import set_shutting_down
        from src.services.whatsapp.state_manager import all_states

        set_shutting_down(True)

        for sid, st in all_states().items():
            client = st.client
            if not client:
                continue
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, _safe_disconnect, client),
                    timeout=3.0,
                )
                logger.info(f"✅ WhatsApp client disconnected (session={sid})")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Disconnect timed out for session={sid}")
        return
    except Exception as e:
        logger.warning(f"WhatsApp shutdown error (non-fatal): {e}")
    finally:
        # Go runtime threads (neonize/cgo) are non-daemon and block process exit.
        # os._exit bypasses Python cleanup and kills all threads immediately,
        # letting the uvicorn reloader spawn a fresh worker cleanly.
        os._exit(0)


async def _media_cleanup_loop():
    while True:
        await asyncio.sleep(3600)
        try:
            from src.services.media.auto_cleanup import run_media_cleanup
            await run_media_cleanup()
        except Exception as e:
            logger.warning(f"Media cleanup error: {e}")


async def _logs_cleanup_loop():
    # Run once at startup to compress yesterday's log, then daily
    try:
        from src.services.logs_cleanup import run_logs_cleanup
        await run_logs_cleanup()
    except Exception as e:
        logger.warning(f"Log cleanup error: {e}")
    while True:
        await asyncio.sleep(86400)  # 24h
        try:
            from src.services.logs_cleanup import run_logs_cleanup
            await run_logs_cleanup()
        except Exception as e:
            logger.warning(f"Log cleanup error: {e}")


def _safe_disconnect(client):
    try:
        client.disconnect()
    except Exception:
        pass
