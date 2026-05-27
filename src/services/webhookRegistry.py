import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.config.constants import DATA_DIR
from src.utils.logger import logger

WEBHOOKS_DIR = Path(DATA_DIR) / "webhooks"

ALL_EVENTS = [
    "message.text",
    "message.image",
    "message.video",
    "message.audio",
    "message.document",
    "message.sticker",
    "message.contact",
    "message.location",
    "message.reaction",
    "message.poll_created",
    "message.poll_vote",
    "message.button_reply",
    "message.list_reply",
    "message.deleted",
    "message.unknown",
    "message.sent",
    "connection.connected",
    "connection.disconnected",
    "connection.qr_ready",
    "call.received",
]


def _ensure_dir():
    WEBHOOKS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "-", name).strip("-")
    return slug[:64]


def _webhook_path(name: str) -> Path:
    return WEBHOOKS_DIR / f"{_slugify(name)}.json"


def _read_file(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else None
    except Exception as e:
        logger.error(f"Erro ao ler webhook {path}: {e}")
        return None


def _write_file(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_webhooks() -> list[dict]:
    _ensure_dir()
    result = []
    for f in sorted(WEBHOOKS_DIR.glob("*.json")):
        wh = _read_file(f)
        if wh:
            result.append(wh)
    return result


def get_webhook(name: str) -> dict | None:
    return _read_file(_webhook_path(name))


def create_webhook(data: dict) -> dict:
    _ensure_dir()
    name = _slugify(data.get("name", ""))
    if not name:
        raise ValueError("name é obrigatório")

    path = _webhook_path(name)
    if path.exists():
        raise ValueError(f"Webhook '{name}' já existe. Use PUT para editar.")

    wh = {
        "name": name,
        "url": data["url"],
        "method": data.get("method", "POST"),
        "headers": data.get("headers", {}),
        "body": data.get("body", {}),
        "events": data.get("events", ["*"]),
        "active": data.get("active", True),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _write_file(path, wh)
    logger.info(f"🔗 Webhook criado: {name}")
    return wh


def update_webhook(name: str, data: dict) -> dict:
    path = _webhook_path(name)
    wh = _read_file(path)
    if not wh:
        raise ValueError(f"Webhook '{name}' não encontrado")

    if "url" in data:
        wh["url"] = data["url"]
    if "method" in data:
        wh["method"] = data["method"]
    if "headers" in data and data["headers"] is not None:
        wh["headers"] = data["headers"]
    if "body" in data and data["body"] is not None:
        wh["body"] = data["body"]
    if "events" in data and data["events"] is not None:
        wh["events"] = data["events"]
    if "active" in data and data["active"] is not None:
        wh["active"] = data["active"]

    _write_file(path, wh)
    logger.info(f"🔗 Webhook atualizado: {name}")
    return wh


def delete_webhook(name: str):
    path = _webhook_path(name)
    if not path.exists():
        raise ValueError(f"Webhook '{name}' não encontrado")
    path.unlink()
    logger.info(f"🗑️ Webhook removido: {name}")


def toggle_webhook(name: str, active: bool) -> dict:
    path = _webhook_path(name)
    wh = _read_file(path)
    if not wh:
        raise ValueError(f"Webhook '{name}' não encontrado")
    wh["active"] = active
    _write_file(path, wh)
    status = "ativado" if active else "desativado"
    logger.info(f"🔗 Webhook {status}: {name}")
    return wh


def get_active_webhooks_for_event(event_type: str) -> list[dict]:
    result = []
    for wh in list_webhooks():
        if not wh.get("active", True):
            continue
        events = wh.get("events", ["*"])
        if "*" in events or event_type in events:
            result.append(wh)
    return result
