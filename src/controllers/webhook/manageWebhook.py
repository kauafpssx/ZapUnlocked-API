from fastapi import HTTPException
from src.services import webhookConfig
from src.utils.logger import logger
from .schemas import WebhookConfigIn, WebhookToggleIn

def configure_webhook(data: WebhookConfigIn):
    if not data.url:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'url' is required."})

    config = webhookConfig.save_webhook_config(data.dict())
    logger.info("🔗 Webhook global configurado com sucesso.")
    return {"success": True, "message": "Webhook configured.", "config": config}

def toggle_webhook(data: WebhookToggleIn):
    status = data.status
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": "'status' must be 'on' or 'off'."})

    enabled = (status == "on")
    try:
        config = webhookConfig.toggle_webhook(enabled)
        logger.info(f"🔗 Webhook global {'ATIVADO' if enabled else 'DESATIVADO'}.")
        return {"success": True, "message": f"Webhook {status}.", "config": config}
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": str(e)})

def delete_webhook():
    try:
        webhookConfig.delete_webhook_config()
        logger.info("🔗 Webhook global removido.")
        return {"success": True, "message": "Webhook removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
