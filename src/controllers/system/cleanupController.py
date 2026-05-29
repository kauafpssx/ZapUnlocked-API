"""Controller for disk cleanup and configuration operations."""

from typing import Dict, Any
from fastapi import HTTPException
from src.config.constants import temp_dir, data_dir
from src.utils.logger import logger
import os
import shutil
import json


async def force_cleanup():
    """Delete all temporary media files."""
    try:
        if temp_dir.exists():
            for filename in os.listdir(temp_dir):
                filepath = temp_dir / filename
                if filepath.is_file() or filepath.is_symlink():
                    filepath.unlink()
                elif filepath.is_dir():
                    shutil.rmtree(filepath)

        return {"success": True, "message": "Temporary files cleared successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to run forced cleanup: {str(e)}"}
        )


async def get_cleanup_settings():
    """Return current automatic database cleanup settings."""
    try:
        db_config_file = data_dir / "db_config.json"

        settings = {"interval": 1440, "last_run": 0}

        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                data = json.load(f)
                settings.update(data)

        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to read cleanup settings: {str(e)}"}
        )


async def update_cleanup_settings(settings: Dict[str, Any]):
    """Update the automatic database cleanup interval."""
    try:
        db_config_file = data_dir / "db_config.json"

        current = {"interval": 1440, "last_run": 0}
        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                current.update(json.load(f))

        if "interval" in settings:
            current["interval"] = int(settings["interval"])

        with open(db_config_file, "w") as f:
            json.dump(current, f)

        return {"success": True, "settings": current}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "INTERNAL_ERROR", "message": f"Failed to save cleanup settings: {str(e)}"}
        )
