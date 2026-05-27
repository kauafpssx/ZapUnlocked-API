from fastapi import HTTPException

from src.services import webhookRegistry
from src.services.webhookRegistry import ALL_EVENTS
from src.utils.logger import logger
from .webhookSchemas import WebhookCreateRequest, WebhookUpdateRequest, WebhookToggleRequest


async def list_webhooks():
    webhooks = webhookRegistry.list_webhooks()
    return {"webhooks": webhooks, "total": len(webhooks)}


async def get_webhook(name: str):
    wh = webhookRegistry.get_webhook(name)
    if not wh:
        raise HTTPException(status_code=404, detail=f"Webhook '{name}' não encontrado")
    return wh


async def create_webhook(data: WebhookCreateRequest):
    _validate_events(data.events)
    try:
        wh = webhookRegistry.create_webhook(data.model_dump())
        return {"success": True, "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao criar webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_webhook(name: str, data: WebhookUpdateRequest):
    if data.events is not None:
        _validate_events(data.events)
    try:
        wh = webhookRegistry.update_webhook(name, data.model_dump(exclude_none=True))
        return {"success": True, "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao atualizar webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def delete_webhook(name: str):
    try:
        webhookRegistry.delete_webhook(name)
        return {"success": True, "message": f"Webhook '{name}' removido"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao deletar webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def toggle_webhook(name: str, data: WebhookToggleRequest):
    try:
        wh = webhookRegistry.toggle_webhook(name, data.active)
        status = "ativado" if data.active else "desativado"
        return {"success": True, "message": f"Webhook '{name}' {status}", "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao alternar webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def test_webhook(name: str):
    wh = webhookRegistry.get_webhook(name)
    if not wh:
        raise HTTPException(status_code=404, detail=f"Webhook '{name}' não encontrado")

    from src.services.webhookService import trigger_webhook
    import asyncio
    from datetime import datetime, timezone

    test_payload = {
        "event": "webhook.test",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": {
            "message": "Teste de webhook — ZapUnlocked API",
            "webhook_name": name,
        },
    }
    try:
        await trigger_webhook(wh, {"from": "test", "text": "test"}, default_payload=test_payload)
        return {"success": True, "message": "Payload de teste enviado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def list_events():
    return {"events": ALL_EVENTS}


def _validate_events(events: list[str]):
    if not events:
        raise HTTPException(status_code=400, detail="events não pode ser vazio. Use ['*'] para todos.")
    invalid = [e for e in events if e != "*" and e not in ALL_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Eventos inválidos: {invalid}. Consulte GET /webhooks/events para a lista completa.",
        )
