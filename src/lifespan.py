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

    # ── FFmpeg warmup ───────────────────────────────────────
    _warm_up_ffmpeg()

    # ── WhatsApp bot ────────────────────────────────────────
    await _start_whatsapp()

    logger.info(f"🚀 API running on port {PORT}")
    yield


# ── Internal helpers ────────────────────────────────────────


def _ensure_dirs():
    """Create data directories if they don't exist."""
    Path(AUTH_DIR).mkdir(parents=True, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Auth directory: {AUTH_DIR}")
    logger.info(f"📁 Data directory (chats): {DATA_DIR}")


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
    """Start the WhatsApp bot in a background task if enabled."""
    enable = os.getenv("ENABLE_WHATSAPP", "1") == "1"
    if not enable:
        logger.warning("WhatsApp bot disabled (ENABLE_WHATSAPP=0)")
        return

    try:
        from src.services.whatsapp.client import start_bot
        asyncio.create_task(start_bot())
        logger.info("WhatsApp bot started")
    except Exception as e:
        logger.error(f"Failed to start WhatsApp bot: {e}")
