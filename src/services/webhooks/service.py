import hashlib
import hmac
import json
import httpx
from datetime import datetime, timezone

from src.utils.logger import logger


def _sign_payload(secret: str, payload: dict) -> str:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return "sha256=" + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()  # noqa: S324


async def trigger_webhook(config: dict, context: dict, default_payload: dict | None = None, _event: str | None = None, session_id: str = "1"):
    url = config.get("url")
    method = config.get("method", "POST")
    headers = config.get("headers", {})
    body = config.get("body", {})
    secret = config.get("secret")

    if not url:
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def replace_placeholders(data):
        if isinstance(data, str):
            res = data.replace("{{from}}", context.get("from", ""))
            res = res.replace("{{text}}", context.get("text", ""))
            res = res.replace("{{phone}}", context.get("phone", context.get("from", "")))
            res = res.replace("{{requested}}", str(context.get("requested", "0")))
            res = res.replace("{{found}}", str(context.get("found", "0")))
            res = res.replace("{{id}}", context.get("id", ""))
            res = res.replace("{{timestamp}}", timestamp)
            return res
        elif isinstance(data, list):
            return [replace_placeholders(item) for item in data]
        elif isinstance(data, dict):
            return {k: replace_placeholders(v) for k, v in data.items()}
        return data

    final_headers = replace_placeholders(headers)

    if not body and default_payload is not None:
        final_body = default_payload
    else:
        final_body = replace_placeholders(body)

    from src.services.webhooks.logs import record_dispatch
    webhook_name = config.get("name", url)
    event_label = _event or context.get("event", "unknown")

    try:
        logger.info(f"🔗 Triggering webhook: {method} {url}")

        if secret and method in ["POST", "PUT", "PATCH"]:
            final_headers["X-Webhook-Signature"] = _sign_payload(secret, final_body)

        timeout = httpx.Timeout(connect=3.0, read=10.0, write=5.0, pool=5.0)
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            request = client.build_request(
                method=method,
                url=url,
                headers=final_headers,
                json=final_body if method in ["POST", "PUT", "PATCH"] else None
            )
            response = await client.send(request)
            response.raise_for_status()
            logger.info(f"✅ Webhook delivered to {url}")
            record_dispatch(webhook_name, event_label, response.status_code, True, session_id=session_id)

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Webhook delivery failed for {url}: {e}")
        logger.error(f"Status: {e.response.status_code} - Body: {e.response.text}")
        record_dispatch(webhook_name, event_label, e.response.status_code, False, str(e), session_id=session_id)
    except Exception as e:
        logger.error(f"❌ Webhook delivery failed for {url}: {str(e)}")
        record_dispatch(webhook_name, event_label, None, False, str(e), session_id=session_id)
