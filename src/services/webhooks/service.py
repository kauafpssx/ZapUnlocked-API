import httpx
from datetime import datetime, timezone

from src.utils.logger import logger


async def trigger_webhook(config: dict, context: dict, default_payload: dict | None = None):
    url = config.get("url")
    method = config.get("method", "POST")
    headers = config.get("headers", {})
    body = config.get("body", {})

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

    try:
        logger.info(f"🔗 Triggering webhook: {method} {url}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            request = client.build_request(
                method=method,
                url=url,
                headers=final_headers,
                json=final_body if method in ["POST", "PUT", "PATCH"] else None
            )
            response = await client.send(request)
            response.raise_for_status()
            logger.info(f"✅ Webhook delivered to {url}")

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Webhook delivery failed for {url}: {e}")
        logger.error(f"Status: {e.response.status_code} - Body: {e.response.text}")
    except Exception as e:
        logger.error(f"❌ Webhook delivery failed for {url}: {str(e)}")
