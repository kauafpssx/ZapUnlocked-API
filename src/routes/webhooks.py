from fastapi import APIRouter, Depends, Body
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
