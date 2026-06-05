import json
import os
from pathlib import Path
from src.config.constants import DATA_DIR
from src.utils.logger import logger

SETTINGS_FILE = Path(DATA_DIR) / "settings.json"

DEFAULT_SETTINGS = {
    "ip_control_enabled": False,
    # NOTE: IP whitelist/blacklist are now stored in data/ip_rules.json
    # and managed via /settings/ip-rules endpoints.
    # Instance settings
    "call_reject_auto": False,
    "call_reject_message": "I'm unavailable right now. Please send a message.",
    "auto_read_message": False,
}

def get_settings():
    try:
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS.copy()
        
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return DEFAULT_SETTINGS.copy()
            
            loaded = json.loads(content)
            # Ensure all default keys exist
            for key, val in DEFAULT_SETTINGS.items():
                if key not in loaded:
                    loaded[key] = val
            return loaded
    except Exception as e:
        logger.error(f"❌ Failed to read settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    try:
        # Merge with current
        current = get_settings()
        current.update(settings)
        
        # Ensure directory exists
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4)
        return current
    except Exception as e:
        logger.error(f"❌ Failed to save settings: {e}")
        return None
