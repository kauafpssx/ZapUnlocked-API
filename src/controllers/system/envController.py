"""Controller for environment variable operations."""

from typing import Dict, Any
from fastapi import HTTPException
from src.config.constants import BASE_DIR
from src.utils.logger import logger
import os

ENV_PATH = BASE_DIR / ".env"
SENSITIVE_KEYS = ["API_KEY", "DB_PASSWORD", "SESSIONS_KEY", "SECRET_KEY"]


async def get_env_vars():
    """Return environment variables from .env, masking sensitive keys."""
    try:
        from dotenv import dotenv_values

        env_dict = dotenv_values(ENV_PATH)

        filtered_env = {
            k: ("********" if k in SENSITIVE_KEYS else v)
            for k, v in env_dict.items()
        }
        return filtered_env
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to read .env: {str(e)}"})


async def update_env_vars(env_data: Dict[str, str]):
    """Update environment variables in .env and in-process os.environ."""
    try:
        from dotenv import set_key

        if not ENV_PATH.exists():
            ENV_PATH.touch()

        for key, value in env_data.items():
            if key in SENSITIVE_KEYS:
                logger.warning(f"🛡️ Attempt to change sensitive key blocked: {key}")
                continue

            set_key(str(ENV_PATH), key, value)
            os.environ[key] = value

        return {
            "success": True,
            "message": "Environment variables updated. Sensitive keys (API_KEY, etc.) cannot be changed here.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to save .env: {str(e)}"})
