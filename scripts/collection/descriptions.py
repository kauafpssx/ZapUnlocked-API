"""Rich endpoint descriptions in English for Postman/Insomnia Docs tab.

ENDPOINT_DESCRIPTIONS: manual docs for key endpoints.
auto_generate_description(): fallback generator for endpoints without manual docs,
  producing a sensible description from OpenAPI operation metadata.
"""

from typing import Any, Dict, List, Optional


# ── Manual descriptions (keyed by method + path OR just path) ────────────
# When method-specific: "GET /path" or "POST /path".
# When path-only: matches any method on that path.
ENDPOINT_DESCRIPTIONS: Dict[str, str] = {
    # ── Logs ─────────────────────────────────────────────────────────────
    "/logs":
        "Returns server logs with powerful filtering. All parameters are optional query params.\n\n"
        "Filters:\n"
        "- `date` (YYYY-MM-DD): Specific day's logs (default: today)\n"
        "- `from_date` / `to_date` (YYYY-MM-DD): Date range (alternative to `date`)\n"
        "- `from_time` / `to_time` (HH:MM): Time range within the selected dates\n"
        "- `level`: Filter by log level — DEBUG, INFO, WARNING, ERROR, CRITICAL\n"
        "- `search`: Full-text search in log messages (case-insensitive)\n"
        "- `limit`: Max lines to return (default: 200, max: 10000)\n"
        "- `offset`: Skip first N matching lines (for pagination)\n\n"
        "Use `date` OR (`from_date` + `to_date`), never both.\n\n"
        "Response includes `filters` (echo of applied filters), `total`, `returned`, `offset`, and `logs` array.",
    "/logs/files":
        "Lists all available log files with their date and size. Each log file covers one day.\n\n"
        'Response: `{"success": true, "count": N, "files": [{"file": "...", "date": "YYYY-MM-DD", "sizeBytes": N, "sizeFormatted": "..."}]}`',
    "POST /logs/cleanup":
        "Runs log maintenance: compresses old .log files to .gz, then deletes compressed "
        "files that exceed age (LOG_MAX_AGE_DAYS, default 30) or total size (LOG_MAX_SIZE_MB, default 50 MB) limits.\n\n"
        'Response: `{"success": true, "compressed": N, "deleted": N}`',

    # ── Status ───────────────────────────────────────────────────────────
    "/stats":
        "Returns real-time runtime statistics including uptime (seconds + formatted), "
        "connection duration, message counters (sent/received), and webhook fire count. "
        "All counters reset on server restart.\n\n"
        "Response shape:\n"
        '`{"uptime": {"seconds": 3600, "formatted": "1h 0m 0s"}, '
        '"connected": {...}, '
        '"messages": {"sent": 42, "received": 128}, '
        '"webhooks": {"fired": 7}}`',
    "DELETE /stats":
        "Resets all runtime statistics counters (messages sent/received, webhooks fired) "
        "back to zero. Does NOT restart the server or disconnect WhatsApp.\n\n"
        'Response: `{"success": true}`',

    # ── Webhook Stats ─────────────────────────────────────────────────────
    "/stats/webhooks":
        "Returns delivery statistics for all registered webhooks, including fire count "
        "and last-fired timestamp for each.\n\n"
        'Response: `{"total": N, "webhooks": [{"name": "...", "fired": N, "last_fired": "..."}]}`',
    "GET /stats/webhooks/{name}":
        "Returns delivery statistics for a single webhook by name.\n\n"
        'Response: `{"name": "...", "fired": N, "last_fired": "..."}`',
    "DELETE /stats/webhooks":
        "Resets delivery statistics for ALL webhooks. Fire counts go back to zero.\n\n"
        'Response: `{"success": true}`',
    "DELETE /stats/webhooks/{name}":
        "Resets delivery statistics for a single webhook by name.\n\n"
        'Response: `{"success": true}`',
    "/status":
        "Returns general connection and instance status. Use this endpoint to check "
        "whether the WhatsApp client is connected, the server is ready, and the instance name/ID.",
    "/status/health":
        "Simple health-check endpoint. Returns HTTP 200 with a JSON body confirming "
        "the server is alive. Does not check WhatsApp connection status.",
    "/status/readiness":
        "Readiness probe — returns HTTP 200 only when the server has completed its "
        "initialization (WhatsApp client ready). Useful for container orchestration health checks.",
    "/status/memory":
        "Returns current memory usage statistics: RSS, heap total, heap used, "
        "external, and array buffers. Useful for monitoring resource consumption.",
    "/status/stream":
        "Returns the current WhatsApp stream/connection state: connected, "
        "disconnected, connecting, etc.",
    "/status/volume":
        "Returns the volume (data usage) statistics for the current WhatsApp session. "
        "Includes sent/received byte counts.",

    # ── Send ─────────────────────────────────────────────────────────────
    "/send":
        "Sends a plain text message to a WhatsApp contact or group.\n\n"
        "Optional parameters:\n"
        "- `delay_message`: Server-side delay before sending. Can be a number (seconds) "
        'or a range string like "2-5" for random delay.\n'
        "- `delay_typing`: Shows the \"typing…\" indicator for N seconds before sending. "
        "Simulates a human typing.\n"
        "- `mentioned`: Array of phone numbers to @mention in group messages. "
        "Marked via ContextInfo — does NOT add @ symbol in text automatically. "
        "Add @ manually in `message` if you want visible mentions.",
    "/send_bulk":
        "Sends the same text message to multiple WhatsApp contacts in sequence.\n\n"
        "Required:\n"
        "- `phones`: Array of phone numbers (strings) to send the message to\n"
        "- `message`: The text content to send\n\n"
        "Optional:\n"
        "- `delay_message`: Per-message server-side delay before sending\n"
        "- `delay_typing`: Per-message typing indicator duration\n"
        '- `delay_between`: Delay BETWEEN messages (not per-message). Can be a number '
        'or a range like "1-3" for random delay.\n'
        "- `mentioned`: Array of phone numbers to @mention in group messages\n\n"
        "Response: `{\"sent\": N, \"failed\": N, \"results\": [...]}`",

    # ── Media ──────────────────────────────────────────────────────────
    "/send_image":
        "Sends an image message. Accepts either a URL or a file upload.\n\n"
        "Use `url` (text field) to send from a remote URL, or `file` (file field) "
        "to upload from your local machine. If both are provided, `url` takes precedence.\n\n"
        "Optional: `caption` (string), `as_document` (boolean — send as file instead of image), "
        "`delay_message`, `delay_typing`, `mentioned`.",
    "/send_audio":
        "Sends an audio message. Accepts URL or file upload.\n\n"
        "Optional: `ptt` (boolean — send as voice note), `as_document` (boolean), "
        '`format` (string, e.g. "m4a", "ogg"), '
        "`delay_message`, `delay_typing`, `mentioned`.",
    "/send_video":
        "Sends a video message. Accepts URL or file upload.\n\n"
        "Optional: `caption` (string), `as_document` (boolean), "
        "`delay_message`, `delay_typing`, `mentioned`.",
    "/send_document":
        "Sends a document/file message. Accepts URL or file upload.\n\n"
        "Optional: `fileName` (string — overrides the displayed filename), "
        "`caption` (string), `delay_message`, `delay_typing`, `mentioned`.",
    "/send_sticker":
        "Sends a sticker image. Accepts URL or file upload.\n\n"
        "Additional sticker-specific fields:\n"
        "- `pack`: Sticker pack name\n"
        "- `author`: Sticker author\n"
        "- `resize_mode`: 'pad' (add padding) or 'crop' (crop to fit)\n"
        "- `pad_color`: Background color when using pad mode, e.g. 'black', 'white', '#FF0000'\n"
        "- `blur_intensity`: Blur strength for the background padding (int)\n\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/send_gif":
        "Sends an animated GIF. Accepts URL or file upload.\n\n"
        "Optional: `caption` (string), `delay_message`, `delay_typing`, `mentioned`.",

    # ── Location / Contact / Link / Reaction ───────────────────────────
    "/messages/send-location":
        "Sends a geographic location to a WhatsApp chat.\n\n"
        "Required: `lat` (float), `lng` (float).\n"
        "Optional: `name` (string), `address` (string).",
    "/messages/send-contact":
        "Sends a single contact (vCard) to a WhatsApp chat.\n\n"
        "Required: `phone` (recipient), `contactPhone` (contact number), "
        "`contactName` (display name).",
    "/messages/send-contacts":
        "Sends multiple contacts in a single message.\n\n"
        "Required: `phone` (recipient), `contacts` (array of `{name, phone}` objects).",
    "/messages/send-link":
        "Sends a link preview message. WhatsApp will fetch and display a preview "
        "card with the URL's metadata (title, description, image).\n\n"
        "Required: `url` (the link), `message` (text accompanying the link).",
    "/messages/send-reaction":
        "Sends a reaction (emoji) to a specific message.\n\n"
        "Required: `messageId` (the ID of the target message), `emoji` (the emoji to react with). "
        "To remove a reaction, send an empty string as `emoji`.",

    # ── Interactive: Buttons ───────────────────────────────────────────
    "/messages/send-button-list":
        "Sends an interactive button list message. Supports up to 5 buttons of mixed types.\n\n"
        "Button types available:\n"
        "- `quick_reply`: Simple reply button with `buttonText` and `id`\n"
        "- `url`: Opens a URL when tapped (`url` field)\n"
        "- `call`: Initiates a phone call (`callPhone` field)\n"
        "- `otp`: One-time password copy button (`code` field)\n\n"
        "NOTE: PIX buttons are NOT supported in combined lists — use the dedicated "
        "/messages/send-button-pix endpoint instead.\n\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-button-url":
        "Sends a single URL button message. The recipient sees a button that opens "
        "a URL when tapped.\n\n"
        "Required: `url`, `button_text`, `title`, `text`.\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-button-call":
        "Sends a single call button message. The recipient sees a button that initiates "
        "a phone call when tapped.\n\n"
        "Required: `callPhone`, `button_text`, `title`, `text`.\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-button-otp":
        "Sends a one-time password (OTP) button. The recipient can copy the code "
        "with one tap.\n\n"
        "Required: `code`, `button_text`, `title`, `text`.\n"
        "Optional: `footer` (string), `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-button-pix":
        "Sends a PIX payment button (exclusive — cannot be combined with other button types).\n\n"
        "Required:\n"
        "- `pixKey`: The PIX key (email, phone, CPF, CNPJ, or random)\n"
        "- `pixType`: Key type — EMAIL, PHONE, CPF, CNPJ, or RANDOM\n"
        "- `pixValue`: Amount in BRL (float)\n"
        "- `merchantName`: Your business/trading name\n"
        "- `pixCity`: Your city\n\n"
        "Optional: `pixDescription` (string), `button_text`, `title`, `text`, "
        "`delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-button-quick-reply":
        "Sends quick reply buttons (simple reply options shown as buttons).\n\n"
        "Required: `title`, `text`, `buttons` (array of `{text, id}` objects).\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",

    # ── Interactive: Option List ───────────────────────────────────────
    "/messages/send-option-list":
        "Sends an interactive list message with a menu of options. The user taps "
        "the button to expand the list and selects an option.\n\n"
        "Required: `title`, `text`, `options` (array of option objects).\n"
        "Optional: `button_text`, `footer`, `description`, "
        "`delay_message`, `delay_typing`, `mentioned`.",

    # ── Interactive: Poll ──────────────────────────────────────────────
    "/messages/send-poll":
        "Creates and sends a poll to a WhatsApp chat. Recipients can vote on options.\n\n"
        "Required: `name` (poll question), `options` (array of strings, up to 12).\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/send-poll-vote":
        "Votes on an existing poll.\n\n"
        "Required: `options` (array of selected option strings), `pollId` (the poll message ID).\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",

    # ── Interactive: Actions ─────────────────────────────────────────
    "/messages/edit":
        "Edits an existing message. Works only for messages sent by the same bot.\n\n"
        "Required: `messageId`, `message` (new text content).\n"
        "Optional: `delay_message`, `delay_typing`, `mentioned`.",
    "/messages/delete":
        "Deletes a message for everyone (if possible) or for yourself.\n\n"
        "Required: `phone`, `messageId`.",
    "/messages/read":
        "Marks a message (or multiple messages) as read.\n\n"
        "Required: `messageIds` (array of message IDs).",

    # ── AI ───────────────────────────────────────────────────────────────
    "/ai/ask":
        "Sends a text message to Meta AI via WhatsApp and waits for its response.\n\n"
        "The message is forwarded to the Meta AI contact (13135550002@s.whatsapp.net). "
        "The server blocks until a reply is received or the `timeout` is reached.\n\n"
        "Response includes:\n"
        "- `text`: The AI's reply text\n"
        "- `hasImage`: Whether the response includes an image\n"
        "- `messageId`: The WhatsApp message ID of the reply\n\n"
        "Requires an active WhatsApp connection.",
    "/ai/imagine":
        "Generates an image using Meta AI's /imagine feature.\n\n"
        "Internally sends `/imagine {prompt}` to the Meta AI contact and returns "
        "the generated image along with any accompanying text.\n\n"
        "Response shape same as /ai/ask with `hasImage: true` when successful.\n\n"
        "Requires an active WhatsApp connection.",

    # ── Settings ─────────────────────────────────────────────────────────
    "/settings/instance/call-reject-auto":
        "Enables or disables automatic call rejection. When enabled, incoming "
        "calls are automatically rejected and the caller may see a configurable message.",
    "/settings/instance/call-reject-message":
        "Sets the message displayed when a call is automatically rejected. "
        "Only applies when `call-reject-auto` is enabled.",
    "/settings/instance/auto-read-message":
        "Enables or disables automatic read receipts for incoming messages. "
        "When enabled, messages are automatically marked as read upon receipt.",
    "/settings/ip-control":
        "Enables or disables IP-based access control. When enabled, only whitelisted "
        "IPs can access the API. Requests from non-whitelisted IPs are blocked.",
    "/settings/ip-rules/whitelist":
        "Adds an IP address to the whitelist. Requires `ip-control` to be enabled.",
    "/settings/ip-rules/blacklist":
        "Adds an IP address to the blacklist. Requires `ip-control` to be enabled.",

    # ── Instance ─────────────────────────────────────────────────────────
    "/session/pair":
        "Pairs a new device via pairing code. This is an alternative to QR code scanning.\n\n"
        "Required: `phone` (the phone number to pair with, including country code). "
        "The server will request a pairing code from WhatsApp.",
    "/instance/update-name":
        "Updates the display name of this API instance. The name appears in logs "
        "and status responses.",
    "/management/database/config":
        "Updates database cleanup configuration.\n\n"
        "Required: `interval` (cleanup interval in minutes). "
        "Older messages are purged periodically based on this setting.",
    "/management/fetch_messages":
        "Fetches stored messages from the local database.\n\n"
        "Required: `phone` (the chat to fetch from).\n"
        "Optional: `limit` (max messages to return, default 20).",
    "/management/recent_contacts":
        "Returns the most recent contacts/chats the bot has interacted with.\n\n"
        "Optional: `limit` (max contacts to return, default 20).",

    # ── Webhooks ─────────────────────────────────────────────────────────
    "/webhooks":
        "Creates a new webhook endpoint. The server will POST event data to this URL "
        "whenever matching events occur.\n\n"
        "Required: `name`, `url` (your endpoint URL), `events` (array of event names "
        'or ["*"] for all events), `active` (boolean).\n\n'
        "Available events:\n"
        "- `message.*` — All message events\n"
        "- `message.text`, `message.image`, `message.audio`, etc.\n"
        "- `message.contacts` — Contact array messages\n"
        "- `status.*` — Status changes\n"
        "- `qr.*` — QR code events\n"
        "- `call.*` — Call events",

    # ── Webhooks ──────────────────────────────────────────────────────────
    "/webhooks/{name}/test":
        "Sends a test payload to a registered webhook URL to verify connectivity and payload format.\n\n"
        "Optional body — specify an `event` to choose which payload template to send. If omitted, "
        "defaults to `message.text`.\n\n"
        "Available event types:\n"
        "- `message.text`, `message.image`, `message.video`, `message.audio`, `message.document`\n"
        "- `message.sticker`, `message.reaction`, `message.location`\n"
        "- `message.button_reply`, `message.list_reply`, `message.deleted`\n"
        "- `message.poll_created`, `message.poll_vote`\n"
        "- `message.sent`, `message.delivered`, `message.read`\n"
        "- `connection.connected`, `connection.disconnected`, `connection.qr_ready`\n"
        "- `group.join`, `contact.presence`, `contact.chat_presence`\n"
        "- `call.received`, `media.cleanup.completed`, `ai.response`\n\n"
        "Example body:\n"
        '```json\n{"event": "message.image"}\n```\n\n'
        "Response includes the HTTP `statusCode` and `response` body from the target URL.",

    # ── System ───────────────────────────────────────────────────────────
    "/system/env":
        "Updates environment variables at runtime. Changes take effect immediately "
        "without server restart.\n\n"
        "Required: key-value pairs of environment variables to update (e.g. `{\"PORT\": \"8300\"}`).",
}


def auto_generate_description(
    method: str,
    path: str,
    summary: str,
    operation: dict,
) -> str:
    """Generate a sensible description for any endpoint that lacks a manual one.

    Uses OpenAPI metadata (summary, description, parameter names, request body)
    to build a concise English description.
    """
    parts = []

    # Use summary if available
    if summary:
        parts.append(summary.rstrip(".") + ".")
    else:
        verb_map = {
            "GET": "Retrieves",
            "POST": "Creates or processes",
            "PUT": "Updates",
            "DELETE": "Deletes",
            "PATCH": "Partially updates",
        }
        verb = verb_map.get(method, method)
        resource = path.strip("/").replace("/", " ").replace("-", " ").replace("_", " ").title()
        parts.append(f"{verb} {resource}.")

    # Add parameter info from OpenAPI
    params = operation.get("parameters", [])
    body = operation.get("requestBody", {})

    param_details = []

    # Path params
    path_params = [p for p in params if p.get("in") == "path"]
    if path_params:
        names = [f"`{p['name']}`" for p in path_params]
        param_details.append(f"Path parameters: {', '.join(names)}")

    # Query params
    query_params = [p for p in params if p.get("in") == "query"]
    if query_params:
        names = [f"`{p['name']}`" for p in query_params]
        param_details.append(f"Query parameters: {', '.join(names)}")

    # Request body fields
    if body:
        content = body.get("content", {})
        for media_type, media_obj in content.items():
            schema = media_obj.get("schema", {})
            if "$ref" in schema:
                # Try to get a name from the $ref
                ref_name = schema["$ref"].split("/")[-1]
                readable = ref_name.replace("Request", "").replace("_", " ").strip()
                param_details.append(f"Request body: `{readable}` schema")
                break
            props = schema.get("properties", {})
            if props:
                required = set(schema.get("required", []))
                field_list = []
                for fname, fprops in props.items():
                    req_mark = " (required)" if fname in required else ""
                    ftype = fprops.get("type", "any")
                    field_list.append(f"`{fname}`: {ftype}{req_mark}")
                if field_list:
                    param_details.append("Fields: " + ", ".join(field_list[:8]))
                    if len(field_list) > 8:
                        param_details[-1] += f" and {len(field_list) - 8} more"

    if param_details:
        parts.append("\n\n" + "\n".join(param_details))

    description = operation.get("description", "")
    if description and description != summary:
        parts.append(f"\n\n{description}")

    return "".join(parts)
