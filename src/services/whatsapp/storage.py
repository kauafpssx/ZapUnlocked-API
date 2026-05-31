import json
import gzip
import re
from pathlib import Path

from src.utils.logger import logger
from src.config.constants import DATA_DIR

CHATS_DIR = Path(DATA_DIR) / "chats"
INDEX_FILE = CHATS_DIR / "index.json"

# Ensure directories exist
CHATS_DIR.mkdir(parents=True, exist_ok=True)

# Max messages stored per chat on disk — kept low to conserve RAM
HISTORY_LIMIT = 20

async def save_chat_index(chat_info: dict):
    try:
        index = {}
        if INDEX_FILE.exists():
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    index = json.loads(content)

        # Basic LID resolution approach
        real_phone = chat_info.get("phone")
        chat_id = chat_info.get("id")

        if not real_phone and chat_id:
            real_phone = chat_id.split("@")[0]

        if chat_id:
            # Update metadata
            if chat_id in index:
                index[chat_id].update(chat_info)
            else:
                index[chat_id] = chat_info

            # Save
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)

    except Exception as err:
        logger.error(f"❌ Failed to save chat index: {str(err)}")

def get_recent_chats_from_index() -> list:
    try:
        if not INDEX_FILE.exists():
            return []

        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if not content:
                return []
            index = json.loads(content)

        chats = list(index.values())
        return sorted(chats, key=lambda x: x.get("lastMessageTimestamp", 0) or 0, reverse=True)
    except Exception as err:
        logger.error(f"❌ Failed to read chat index: {str(err)}")
        return []

async def add_message_to_history(phone: str, message: dict):
    if not phone:
        return

    # Security sanitization: strip directory traversal characters
    safe_phone = re.sub(r'[^a-zA-Z0-9_\-\.]', '', phone)
    
    file_name = f"{safe_phone}.json.gz"
    file_path = CHATS_DIR / file_name
    history = []

    try:
        if file_path.exists():
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                content = f.read()
                if content:
                    history = json.loads(content)

        # Avoid duplicates based on ID
        msg_id = message.get("key", {}).get("id")
        if not any(m.get("key", {}).get("id") == msg_id for m in history):
            history.append(message)

        # Keep limit
        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

        # Compress and save
        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            json.dump(history, f)

    except Exception as err:
        logger.error(f"❌ Failed to save history for {phone}: {str(err)}")

async def get_history(phone: str) -> list:
    if not phone:
        return []

    safe_phone = re.sub(r'[^a-zA-Z0-9_\-\.]', '', phone)
    file_name = f"{safe_phone}.json.gz"
    file_path = CHATS_DIR / file_name

    try:
        if not file_path.exists():
            return []

        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            content = f.read()
            if content:
                return json.loads(content)
        return []
    except Exception as err:
        logger.error(f"❌ Failed to read history for {phone}: {str(err)}")
        return []

async def clear_all_data():
    try:
        if CHATS_DIR.exists():
            for file in CHATS_DIR.iterdir():
                if file.is_file():
                    file.unlink()
            logger.info("🧹 All chat history data cleared successfully.")
    except Exception as err:
        logger.error(f"❌ Failed to clear chat data: {str(err)}")
