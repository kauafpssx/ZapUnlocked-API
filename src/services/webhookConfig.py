import json
from pathlib import Path

from src.config.constants import DATA_DIR
from src.utils.logger import logger

CHATS_DIR = Path(DATA_DIR) / "chats"
WEBHOOK_FILE = CHATS_DIR / "webhook.json"

CHATS_DIR.mkdir(parents=True, exist_ok=True)

def save_webhook_config(config: dict) -> dict:
    current = get_webhook_config()

    enabled = config.get("enabled")
    if enabled is None:
        enabled = current.get("enabled", True) if current else True

    final_config = {
        "enabled": enabled,
        "url": config.get("url"),
        "method": config.get("method", "POST"),
        "headers": config.get("headers", {}),
        "body": config.get("body", {})
    }

    with open(WEBHOOK_FILE, "w", encoding="utf-8") as f:
        json.dump(final_config, f, indent=2)

    return final_config

def get_webhook_config():
    try:
        if not WEBHOOK_FILE.exists():
            return None
        with open(WEBHOOK_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if content:
                return json.loads(content)
        return None
    except Exception:
        return None

def toggle_webhook(status: bool) -> dict:
    config = get_webhook_config()
    if not config:
        raise Exception("Webhook not configured yet. Use the configuration route first.")

    config["enabled"] = status
    with open(WEBHOOK_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return config

def delete_webhook_config():
    try:
        if WEBHOOK_FILE.exists():
            WEBHOOK_FILE.unlink()
    except Exception as e:
        logger.error(f"Failed to delete webhook.json: {e}")
