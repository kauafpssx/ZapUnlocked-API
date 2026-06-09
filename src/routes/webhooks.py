from fastapi import APIRouter, Depends, Body, Query
from typing import Optional
from src.middleware.auth import auth
from src.controllers.webhook.webhookCrudController import (
    list_webhooks,
    get_webhook,
    create_webhook,
    update_webhook,
    delete_webhook,
    toggle_webhook,
    test_webhook,
    list_events,
)
from src.services.webhooks.logs import get_logs as _get_wh_logs, delete_logs as _del_wh_logs

router = APIRouter(dependencies=[Depends(auth)])

router.get("/events")(list_events)
router.get("")(list_webhooks)
router.post("")(create_webhook)
router.get("/{name}")(get_webhook)
router.put("/{name}")(update_webhook)
router.delete("/{name}")(delete_webhook)
router.post("/{name}/toggle")(toggle_webhook)

@router.post("/{name}/test")
async def test_webhook_route(name: str, data: Optional[dict] = Body(default=None)):
    return await test_webhook(name, data)


@router.get("/{name}/logs")
async def webhook_logs(name: str, limit: int = Query(default=50, ge=1, le=100)):
    logs = _get_wh_logs(name, limit)
    return {"success": True, "webhook": name, "total": len(logs), "logs": logs}


@router.delete("/{name}/logs")
async def delete_webhook_logs(name: str):
    _del_wh_logs(name)
    return {"success": True, "message": f"Logs cleared for webhook '{name}'."}


@router.delete("/logs/all")
async def delete_all_webhook_logs():
    _del_wh_logs()
    return {"success": True, "message": "All webhook logs cleared."}
