import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from src.config.constants import DATA_DIR
from src.services.webhooks import registry as webhook_registry
from src.services.whatsapp.settingsService import get_settings, save_settings
from src.utils.logger import logger

_IP_RULES_FILE = Path(DATA_DIR) / "ip_rules.json"


def _read_ip_rules() -> dict:
    try:
        if _IP_RULES_FILE.exists():
            return json.loads(_IP_RULES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_ip_rules(data: dict) -> None:
    _IP_RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    _IP_RULES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def export_config():
    webhooks = webhook_registry.list_webhooks()
    settings = get_settings()
    ip_rules = _read_ip_rules()

    payload = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": 1,
        "webhooks": webhooks,
        "settings": settings,
        "ip_rules": ip_rules,
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": "attachment; filename=zapunlocked-config.json"},
    )


async def import_config(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FILE", "message": "File is not valid JSON."})

    if data.get("version") != 1:
        raise HTTPException(status_code=400, detail={"error": "UNSUPPORTED_VERSION", "message": "Only version 1 exports are supported."})

    results = {"webhooks_imported": 0, "webhooks_skipped": 0, "settings": False, "ip_rules": False}

    # Webhooks — upsert: update if exists, create if not
    for wh in data.get("webhooks", []):
        name = wh.get("name")
        if not name:
            continue
        try:
            if webhook_registry.get_webhook(name):
                webhook_registry.update_webhook(name, wh)
            else:
                webhook_registry.create_webhook(wh)
            results["webhooks_imported"] += 1
        except Exception as e:
            logger.warning(f"Import: skipped webhook '{name}': {e}")
            results["webhooks_skipped"] += 1

    # Settings
    if "settings" in data and isinstance(data["settings"], dict):
        save_settings(data["settings"])
        results["settings"] = True

    # IP rules
    if "ip_rules" in data and isinstance(data["ip_rules"], dict):
        _write_ip_rules(data["ip_rules"])
        results["ip_rules"] = True

    logger.info(f"Config imported: {results}")
    return {"success": True, "imported": results}
