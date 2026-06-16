import json
import gzip
import re
from pathlib import Path

from src.utils.logger import logger
from src.utils.db import get_conn
from src.config.constants import DATA_DIR

CHATS_DIR = Path(DATA_DIR) / "chats"  # legacy fallback for tests

HISTORY_LIMIT = 20


def _chats_dir(session_id: str = "1") -> Path:
    from src.config.constants import get_data_dir
    d = Path(get_data_dir(session_id)) / "chats"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def save_chat_index(chat_info: dict, session_id: str = "1") -> None:
    try:
        chat_id = chat_info.get("id")
        if not chat_id:
            return

        phone = chat_info.get("phone")
        if not phone:
            phone = chat_id.split("@")[0]

        name = chat_info.get("name")
        ts = chat_info.get("lastMessageTimestamp", 0) or 0

        conn = get_conn()
        conn.execute(
            """INSERT INTO chat_index
                   (session_id, chat_id, phone, name, last_message_timestamp)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(session_id, chat_id) DO UPDATE SET
                   phone = excluded.phone,
                   name = excluded.name,
                   last_message_timestamp = excluded.last_message_timestamp""",
            (session_id, chat_id, phone, name, ts),
        )
        conn.commit()
    except Exception as err:
        logger.error(f"❌ Failed to save chat index: {err}")


def get_recent_chats_from_index(session_id: str = "1") -> list:
    try:
        conn = get_conn()
        rows = conn.execute(
            """SELECT chat_id, phone, name, last_message_timestamp
               FROM chat_index
               WHERE session_id=?
               ORDER BY last_message_timestamp DESC""",
            (session_id,),
        ).fetchall()
        return [
            {
                "id": row["chat_id"],
                "phone": row["phone"],
                "name": row["name"],
                "lastMessageTimestamp": row["last_message_timestamp"],
            }
            for row in rows
        ]
    except Exception as err:
        logger.error(f"❌ Failed to read chat index: {err}")
        return []


async def add_message_to_history(phone: str, message: dict, session_id: str = "1") -> None:
    if not phone:
        return

    safe_phone = re.sub(r'[^a-zA-Z0-9_\-\.]', '', phone)
    file_path = _chats_dir(session_id) / f"{safe_phone}.json.gz"
    history = []

    try:
        if file_path.exists():
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                content = f.read()
                if content:
                    history = json.loads(content)

        msg_id = message.get("key", {}).get("id")
        if not any(m.get("key", {}).get("id") == msg_id for m in history):
            history.append(message)

        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            json.dump(history, f)

    except Exception as err:
        logger.error(f"❌ Failed to save history for {phone}: {err}")


async def get_history(phone: str, session_id: str = "1") -> list:
    if not phone:
        return []

    safe_phone = re.sub(r'[^a-zA-Z0-9_\-\.]', '', phone)
    file_path = _chats_dir(session_id) / f"{safe_phone}.json.gz"

    try:
        if not file_path.exists():
            return []
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            content = f.read()
            if content:
                return json.loads(content)
        return []
    except Exception as err:
        logger.error(f"❌ Failed to read history for {phone}: {err}")
        return []


async def clear_all_data(session_id: str = "1") -> None:
    try:
        chats = _chats_dir(session_id)
        if chats.exists():
            for file in chats.iterdir():
                if file.is_file():
                    file.unlink()
        conn = get_conn()
        conn.execute("DELETE FROM chat_index WHERE session_id=?", (session_id,))
        conn.commit()
        logger.info(f"🧹 All chat history data cleared (session={session_id}).")
    except Exception as err:
        logger.error(f"❌ Failed to clear chat data: {err}")
