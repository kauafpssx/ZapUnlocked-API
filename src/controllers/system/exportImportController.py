from src.utils.decorators import get_session_id
import json
from datetime import datetime, timezone
from fastapi import HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse

from src.services.ip_rules_service import get_ip_rules, add_ip
from src.services.webhooks import registry as webhook_registry
from src.services.whatsapp.settingsService import get_settings, save_settings
from src.utils.logger import logger


async def export_config(request: Request):
    sid = get_session_id(request)
    webhooks = webhook_registry.list_webhooks(sid)
    settings = get_settings(sid)
    ip_rules = get_ip_rules()

    payload = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": 1,
        "session_id": sid,
        "webhooks": webhooks,
        "settings": settings,
        "ip_rules": ip_rules,
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": "attachment; filename=zapunlocked-config.json"},
    )


async def import_config(file: UploadFile = File(...), request: Request = None):
    sid = get_session_id(request)
    raw = await file.read()
    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FILE", "message": "File is not valid JSON."})

    if data.get("version") != 1:
        raise HTTPException(status_code=400, detail={"error": "UNSUPPORTED_VERSION", "message": "Only version 1 exports are supported."})

    results = {"webhooks_imported": 0, "webhooks_skipped": 0, "settings": False, "ip_rules": False}

    for wh in data.get("webhooks", []):
        name = wh.get("name")
        if not name:
            continue
        try:
            if webhook_registry.get_webhook(name, sid):
                webhook_registry.update_webhook(name, wh, sid)
            else:
                webhook_registry.create_webhook(wh, sid)
            results["webhooks_imported"] += 1
        except Exception as e:
            logger.warning(f"Import: skipped webhook '{name}': {e}")
            results["webhooks_skipped"] += 1

    if "settings" in data and isinstance(data["settings"], dict):
        save_settings(data["settings"], sid)
        results["settings"] = True

    if "ip_rules" in data and isinstance(data["ip_rules"], dict):
        for list_name in ("whitelist", "blacklist"):
            for ip in data["ip_rules"].get(list_name, []):
                try:
                    add_ip(list_name, ip)
                except Exception:
                    pass
        results["ip_rules"] = True

    logger.info(f"Config imported for session={sid}: {results}")
    return {"success": True, "imported": results}
