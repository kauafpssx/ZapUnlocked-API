from fastapi import HTTPException
from src.services import webhookConfig
from src.utils.logger import logger
from .schemas import WebhookConfigIn, WebhookToggleIn

def configure_webhook(data: WebhookConfigIn):
    if not data.url:
        raise HTTPException(status_code=400, detail="URL é obrigatória")

    config = webhookConfig.save_webhook_config(data.dict())
    logger.info("🔗 Webhook global configurado com sucesso.")
    return {"success": True, "message": "Webhook configurado", "config": config}

def toggle_webhook(data: WebhookToggleIn):
    status = data.status
    if status not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Status deve ser 'on' ou 'off'")

    enabled = (status == "on")
    try:
        config = webhookConfig.toggle_webhook(enabled)
        state_str = "ATIVADO" if enabled else "DESATIVADO"
        logger.info(f"🔗 Webhook global {state_str}.")
        return {"success": True, "message": f"Webhook {status}", "config": config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def delete_webhook():
    try:
        webhookConfig.delete_webhook_config()
        logger.info("🔗 Webhook global removido.")
        return {"success": True, "message": "Webhook removido e arquivo apagado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
