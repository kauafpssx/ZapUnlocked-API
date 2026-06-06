from fastapi import HTTPException

from src.services import webhookRegistry
from src.services.webhooks.registry import ALL_EVENTS
from src.utils.logger import logger
from src.schemas import WebhookCreateRequest, WebhookUpdateRequest, WebhookToggleRequest


async def list_webhooks():
    webhooks = webhookRegistry.list_webhooks()
    return {"webhooks": webhooks, "total": len(webhooks)}


async def get_webhook(name: str):
    wh = webhookRegistry.get_webhook(name)
    if not wh:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Webhook '{name}' not found."})
    return wh


async def create_webhook(data: WebhookCreateRequest):
    _validate_events(data.events)
    try:
        wh = webhookRegistry.create_webhook(data.model_dump())
        return {"success": True, "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": str(e)})
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def update_webhook(name: str, data: WebhookUpdateRequest):
    if data.events is not None:
        _validate_events(data.events)
    try:
        wh = webhookRegistry.update_webhook(name, data.model_dump(exclude_none=True))
        return {"success": True, "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": str(e)})
    except Exception as e:
        logger.error(f"Failed to update webhook: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def delete_webhook(name: str):
    try:
        webhookRegistry.delete_webhook(name)
        return {"success": True, "message": f"Webhook '{name}' removed."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": str(e)})
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def toggle_webhook(name: str, data: WebhookToggleRequest):
    try:
        wh = webhookRegistry.toggle_webhook(name, data.active)
        status = "enabled" if data.active else "disabled"
        return {"success": True, "message": f"Webhook '{name}' {status}.", "webhook": wh}
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": str(e)})
    except Exception as e:
        logger.error(f"Failed to toggle webhook: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def test_webhook(name: str, data: dict = None):
    from fastapi import Body
    wh = webhookRegistry.get_webhook(name)
    if not wh:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Webhook '{name}' not found."})

    import httpx
    from datetime import datetime, timezone

    event = (data or {}).get("event", "message.text")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "event": event,
        "timestamp": ts,
        "data": _sample_payload(event),
    }

    url = wh.get("url")
    method = wh.get("method", "POST")
    headers = wh.get("headers") or {}

    try:
        timeout = httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=5.0)
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.request(method, url, headers=headers, json=payload)
        return {
            "success": True,
            "event": event,
            "url": url,
            "statusCode": response.status_code,
            "response": response.text[:500] if response.text else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "DELIVERY_FAILED", "message": str(e)})


def _sample_payload(event: str) -> dict:
    base = {
        "messageId": "3EB0TEST000000000001",
        "from": "5511999990000",
        "fromName": "Test User",
        "fromJid": "5511999990000@s.whatsapp.net",
        "isGroup": False,
    }
    samples = {
        "message.text": {**base, "text": "Hello! This is a test message from ZapUnlocked.", "quoted": None},
        "message.image": {**base, "caption": "Test image caption", "mimetype": "image/jpeg", "fileLength": 204800},
        "message.video": {**base, "caption": "Test video", "mimetype": "video/mp4", "fileLength": 5242880, "isPTT": False, "isGif": False},
        "message.audio": {**base, "mimetype": "audio/ogg; codecs=opus", "fileLength": 30720, "isPTT": True, "durationSeconds": 8},
        "message.document": {**base, "fileName": "test-document.pdf", "caption": "Test document", "mimetype": "application/pdf", "fileLength": 102400},
        "message.sticker": {**base, "mimetype": "image/webp", "isAnimated": False},
        "message.reaction": {**base, "emoji": "❤️", "targetMessageId": "3EB0ABCDEF123456", "isRemoved": False},
        "message.location": {**base, "lat": -23.5505, "lng": -46.6333, "name": "Av. Paulista", "address": "Av. Paulista, 1000 — São Paulo"},
        "message.button_reply": {**base, "buttonId": "option_yes", "displayText": "Yes", "type": "quick_reply"},
        "message.list_reply": {**base, "rowId": "1", "title": "Option A", "description": "Selected option"},
        "message.deleted": base,
        "message.poll_created": {**base, "pollName": "Best flavor?", "options": ["Chocolate", "Strawberry", "Vanilla"]},
        "message.poll_vote": {**base, "pollId": "3EB0ABCDEF123456", "selectedOptions": ["Chocolate"]},
        "message.sent": {"to": "5511999990000", "type": "text", "messageId": "3EB0TEST000000000001"},
        "message.delivered": {"from": "5511999990000", "fromJid": "5511999990000@s.whatsapp.net", "messageIds": ["3EB0TEST000000000001"], "type": 1, "timestamp": 1704067200},
        "message.read": {"from": "5511999990000", "fromJid": "5511999990000@s.whatsapp.net", "messageIds": ["3EB0TEST000000000001"], "type": "read", "timestamp": 1704067200},
        "connection.connected": {"phone": "5511999990000"},
        "connection.disconnected": {},
        "connection.qr_ready": {"qr": "2@testqrcode..."},
        "group.join": {"groupId": "120363000000000001@g.us", "groupName": "Test Group", "reason": "invite", "type": ""},
        "contact.presence": {"from": "5511999990000", "fromJid": "5511999990000@s.whatsapp.net", "status": "online", "lastSeen": 0},
        "contact.chat_presence": {"from": "5511999990000", "fromJid": "5511999990000@s.whatsapp.net", "state": "typing", "media": None},
        "call.received": {"from": "5511999990000", "fromJid": "5511999990000@s.whatsapp.net", "callId": "TESTCALL001"},
        "media.cleanup.completed": {"filesRemoved": 3, "remainingBytes": 52428800},
        "ai.response": {"text": "Brasília is the capital of Brazil.", "hasImage": False, "imageBase64": None, "imageUrl": None, "mimeType": None, "messageId": "3EB0TEST000000000001"},
    }
    return samples.get(event, {"message": f"Test payload for event '{event}'", "webhook_name": "test"})


async def list_events():
    return {"events": ALL_EVENTS}


def _validate_events(events: list[str]):
    if not events:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'events' cannot be empty. Use ['*'] for all events."})
    invalid = [e for e in events if e != "*" and e not in ALL_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_FIELD", "message": f"Invalid events: {invalid}. See GET /webhooks/events for the full list."},
        )
