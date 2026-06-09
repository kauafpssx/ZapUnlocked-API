"""Rich endpoint descriptions in English for Postman/Insomnia Docs tab.

ENDPOINT_DESCRIPTIONS: manual docs for all endpoints.
auto_generate_description(): fallback for any endpoint without manual docs.
"""

from typing import Any, Dict, List, Optional


# ── Shared optional fields note ────────────────────────────────────────────
# Used by all message-sending endpoints that extend BaseWhatsAppRequest.
# These fields are shown as // comments in the request body — uncomment to use.

_OPTIONAL_NOTE = """\
Optional: delay_message, delay_typing, mentioned, quoted_id (by ID), type ("text" or "id").
- delay_message: server-side delay (seconds or range like "2-5")
- delay_typing: shows typing indicator for N seconds
- mentioned: array of phones to @mention in groups
- quoted_id: reply to message by exact message ID
- type: "id" (match by ID, default) or "text" (match by text content)"""

_OPTIONAL_FORM_NOTE = """\
Optional: delay_message, delay_typing, mentioned, reply (by text), quoted_id (by ID).
Note: Media endpoints do NOT have a type field.
- delay_message: server-side delay (seconds or range like "2-5")
- delay_typing: shows typing indicator for N seconds
- mentioned: array of phones to @mention in groups
- reply: reply to message by matching text content
- quoted_id: reply to message by exact message ID"""


def _with_options(desc: str) -> str:
    """Append the optional fields note to a description."""
    return desc + "\n\n" + _OPTIONAL_NOTE

def _with_form_options(desc: str) -> str:
    """Append the formdata optional fields note (no type) to a description."""
    return desc + "\n\n" + _OPTIONAL_FORM_NOTE


# ── Manual descriptions (keyed by method + path OR just path) ────────────
ENDPOINT_DESCRIPTIONS: Dict[str, str] = {

    # ═════════════════════════════════════════════════════════════════════
    # LOGS
    # ═════════════════════════════════════════════════════════════════════
    "/logs":
        "Returns server logs with powerful filtering. All filter parameters below "
        "are optional query params — use as many or as few as needed.\n\n"
        "Date filters (use `date` OR `from_date`+`to_date`, never both):\n"
        "- `date` (YYYY-MM-DD): Specific day's logs (default: today)\n"
        "- `from_date` / `to_date` (YYYY-MM-DD): Date range\n\n"
        "Time filter (refines within the selected date(s)):\n"
        "- `from_time` / `to_time` (HH:MM): Time range\n\n"
        "Content filters:\n"
        "- `level`: Log level — `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`\n"
        "- `search`: Case-insensitive full-text search in log messages\n\n"
        "Pagination:\n"
        "- `limit`: Max lines to return (default: 200, max: 10000)\n"
        "- `offset`: Skip first N matching lines\n\n"
        "Response: `{\"success\": true, \"filters\": {...}, \"total\": N, \"returned\": N, \"offset\": N, \"logs\": [...]}`",
    "/logs/files":
        "Lists all available log files with their date, size in bytes, and a human-readable "
        "size string. Each file covers one day (zapunlocked_YYYY-MM-DD.log).\n\n"
        "Response:\n"
        '`{"success": true, "count": N, "files": [{"file": "...", "date": "YYYY-MM-DD", "sizeBytes": N, "sizeFormatted": "..."}]}`',
    "POST /logs/cleanup":
        "Runs log maintenance in two steps:\n"
        "1. **Compress** — older .log files (not today's) are gzip-compressed to .log.gz\n"
        "2. **Cleanup** — compressed files are deleted if they exceed age (LOG_MAX_AGE_DAYS, "
        "default 30) or total log directory size (LOG_MAX_SIZE_MB, default 50 MB)\n\n"
        "Response: `{\"success\": true, \"compressed\": N, \"deleted\": N}`",

    # ═════════════════════════════════════════════════════════════════════
    # STATUS
    # ═════════════════════════════════════════════════════════════════════
    "/stats":
        "Returns real-time runtime statistics accumulated since the server started:\n\n"
        "- **uptime**: seconds + human-readable uptime string\n"
        "- **connected**: duration of the current WhatsApp connection (if connected)\n"
        "- **messages**: total sent/received count\n"
        "- **webhooks**: total webhook events fired\n\n"
        "Response example:\n"
        '`{"uptime": {"seconds": 3600, "formatted": "1h 0m 0s"}, '
        '"connected": {...}, '
        '"messages": {"sent": 42, "received": 128}, '
        '"webhooks": {"fired": 7}}`',
    "DELETE /stats":
        "Resets all runtime counters (messages sent/received, webhooks fired) back to zero. "
        "The server continues running — only the in-memory + persisted counters are cleared.\n\n"
        'Response: `{"success": true}`',
    "/stats/webhooks":
        "Returns per-webhook delivery statistics: how many times each webhook was fired "
        "and the timestamp of the last fire.\n\n"
        "Response:\n"
        '`{"total": N, "webhooks": [{"name": "...", "fired": N, "last_fired": "..."}]}`',
    "GET /stats/webhooks/{name}":
        "Returns delivery stats for a single webhook by name.\n\n"
        'Response: `{"name": "...", "fired": N, "last_fired": "..."}`\n\n'
        "Returns 404 if the webhook name has no recorded stats.",
    "DELETE /stats/webhooks":
        "Resets delivery statistics for ALL webhooks. Each webhook's fired count goes to 0 "
        "and last_fired becomes null.\n\n"
        'Response: `{"success": true}`',
    "DELETE /stats/webhooks/{name}":
        "Resets delivery statistics for a single webhook by name.\n\n"
        'Response: `{"success": true}`\n\n'
        "Returns 404 if the webhook name has no recorded stats.",
    "/status":
        "Returns the current server and WhatsApp connection status: client readiness, "
        "instance name/ID, and connection state (connected/disconnected/connecting).",
    "/status/health":
        "Simple liveness check. Returns HTTP 200 immediately regardless of WhatsApp state. "
        "Use `/status/readiness` for a deeper check.",
    "/status/readiness":
        "Readiness probe. Returns HTTP 200 only after the server has fully initialized "
        "and the WhatsApp client is ready. Useful for container orchestration (Kubernetes, Docker).",
    "/status/memory":
        "Returns memory usage from the Node/V8 heap: RSS, heap total, heap used, "
        "external memory, and array buffers. Useful for resource monitoring.",
    "/status/stream":
        "Returns the current WhatsApp stream/connection state: `connected`, `disconnected`, "
        "`connecting`, etc. Also includes reconnect attempts if applicable.",
    "/status/volume":
        "Returns data usage statistics for the current WhatsApp session, including "
        "bytes sent and received.",

    # ═════════════════════════════════════════════════════════════════════
    # SEND — TEXT
    # ═════════════════════════════════════════════════════════════════════
    "/send": _with_options(
        "Sends a plain text message to a WhatsApp contact or group.\n\n"
        "Required:\n"
        "- `phone` — recipient phone number (or group ID)\n"
        "- `message` — the text content to send"
    ),
    "/send_bulk":
        "Sends the same text message to multiple WhatsApp contacts sequentially.\n\n"
        "Required: phones (array), message (text).\n"
        "Optional: delay_message, delay_typing, mentioned, delay_between (delay between messages, "
        'number or range like "1-3").\n\n'
        "Response includes per-phone results:\n"
        '{"success": true, "sent": N, "failed": N, "results": [{"phone": "...", "success": true/false, "error": "..."}]}',

    # ═════════════════════════════════════════════════════════════════════
    # SEND — MEDIA (multipart/form-data)
    # ═════════════════════════════════════════════════════════════════════
    "/send_image": _with_form_options(
        "Sends an image message. Accepts either a URL or a file upload.\n\n"
        "Use `url` (text field) to send from a remote URL, or `file` (file field) "
        "to upload from your machine. If both are provided, `url` takes precedence.\n\n"
        "Optional: `caption` (string), `as_document` (send as file instead of image, boolean)."
    ),
    "/send_audio": _with_form_options(
        "Sends an audio message. Accepts URL or file upload.\n\n"
        "Use `url` (text) or `file` (upload).\n\n"
        "Optional: `ptt` (send as voice note, boolean), `as_document` (boolean), "
        '`format` (e.g. "m4a", "ogg").'
    ),
    "/send_video": _with_form_options(
        "Sends a video message. Accepts URL or file upload.\n\n"
        "Use `url` (text) or `file` (upload).\n\n"
        "Optional: `caption` (string), `as_document` (boolean)."
    ),
    "/send_document": _with_form_options(
        "Sends a document/file message. Accepts URL or file upload.\n\n"
        "Use `url` (text) or `file` (upload).\n\n"
        "Optional: `fileName` (overrides the displayed filename, string), "
        "`caption` (string)."
    ),
    "/send_sticker": _with_form_options(
        "Sends a sticker image. Accepts URL or file upload.\n\n"
        "Use `url` (text) or `file` (upload).\n\n"
        "Sticker-specific fields:\n"
        "- `pack` — sticker pack name\n"
        "- `author` — sticker author\n"
        "- `resize_mode` — `\"pad\"` (adds padding) or `\"crop\"` (crops to fit)\n"
        "- `pad_color` — background hex/name when using pad mode (e.g. `\"black\"`, `\"#FF0000\"`)\n"
        "- `blur_intensity` — background blur strength when padding (integer)"
    ),
    "/send_gif": _with_form_options(
        "Sends an animated GIF. Accepts URL or file upload.\n\n"
        "Use `url` (text) or `file` (upload).\n\n"
        "Optional: `caption` (string)."
    ),

    # ═════════════════════════════════════════════════════════════════════
    # SEND — LOCATION / CONTACT / LINK / REACTION
    # ═════════════════════════════════════════════════════════════════════
    "/send_location": _with_options(
        "Sends a geographic location pin to a WhatsApp chat.\n\n"
        "Required: phone, lat (float), lng (float).\n"
        "Optional: name (location name), address (street address)."
    ),
    "/send_contact": _with_options(
        "Sends a single contact as a vCard to a WhatsApp chat.\n\n"
        "Required: phone, contactPhone (contact's phone), contactName (display name)."
    ),
    "/send_contacts": _with_options(
        "Sends multiple contacts in a single message.\n\n"
        "Required: phone, contacts — array of {name, phone} objects."
    ),
    "/send_link": _with_options(
        "Sends a message with a link preview. WhatsApp fetches and displays a preview "
        "card (title, description, image) from the URL metadata.\n\n"
        "Required: phone, url (the link), message (text accompanying the link).\n"
        "Optional: title, description, imageUrl for custom preview overrides."
    ),
    "/send_reaction": _with_options(
        "Sends an emoji reaction to a specific message.\n\n"
        "Required: phone, messageId (target message ID), emoji.\n"
        "To remove a reaction, send an empty string as emoji."
    ),

    # ═════════════════════════════════════════════════════════════════════
    # INTERACTIVE — BUTTONS
    # ═════════════════════════════════════════════════════════════════════
    "/messages/send-button-list": _with_options(
        "Sends an interactive message with up to 5 buttons of mixed types.\n\n"
        "Required: `phone`, `message`, `title`, `text`, `buttons`.\n\n"
        "Button types (mix & match):\n"
        "- `quick_reply` — simple tap button with `buttonText` and `id`\n"
        "- `url` — opens a URL when tapped (`url` field)\n"
        "- `call` — initiates a phone call (`callPhone` field)\n"
        "- `otp` — one-time password copy button (`code` field)\n\n"
        "⚠ PIX button is NOT supported in combined lists — use /messages/send-button-pix.\n\n"
        "Button object example:\n"
        '`{"type": "quick_reply", "buttonText": "Yes", "id": "yes"}`'
    ),
    "/messages/send-button-url": _with_options(
        "Sends a single URL button message. Recipient sees a button that opens "
        "a URL when tapped.\n\n"
        "Required: `phone`, `url`, `button_text`, `title`, `text`."
    ),
    "/messages/send-button-call": _with_options(
        "Sends a single call button message. Recipient sees a button that initiates "
        "a phone call when tapped.\n\n"
        "Required: `phone`, `callPhone`, `button_text`, `title`, `text`."
    ),
    "/messages/send-button-otp": _with_options(
        "Sends a one-time password (OTP) button. Recipient can copy the code with "
        "a single tap.\n\n"
        "Required: `phone`, `code`, `button_text`, `title`, `text`.\n"
        "Optional: `footer` (string)."
    ),
    "/messages/send-button-pix": _with_options(
        "Sends a PIX payment button (⚠ exclusive — cannot be combined with other button types).\n\n"
        "Required:\n"
        "- `pixKey` — the PIX key (email, phone, CPF, CNPJ, or random)\n"
        "- `pixType` — key type: `EMAIL`, `PHONE`, `CPF`, `CNPJ`, or `RANDOM`\n"
        "- `pixValue` — amount in BRL (float, e.g. 19.90)\n"
        "- `merchantName` — your business/trading name\n"
        "- `pixCity` — your city\n\n"
        "Optional: `pixDescription`, `button_text`, `title`, `text`."
    ),
    "/messages/send-button-quick-reply": _with_options(
        "Sends one or more quick reply buttons — simple tap options.\n\n"
        "Required: `phone`, `title`, `text`, `buttons` — array of "
        '`{"text": "...", "id": "..."}` objects.'
    ),

    # ═════════════════════════════════════════════════════════════════════
    # INTERACTIVE — OPTION LIST
    # ═════════════════════════════════════════════════════════════════════
    "/messages/send-option-list": _with_options(
        "Sends an interactive list message. Recipient taps a button to expand "
        "a menu and selects one option.\n\n"
        "Required: `phone`, `title`, `text`, `options` — array of "
        '`{"title": "...", "description": "..."}` objects.\n\n'
        "Optional: `button_text` (the expand button label), `footer`, `description`."
    ),

    # ═════════════════════════════════════════════════════════════════════
    # INTERACTIVE — POLL
    # ═════════════════════════════════════════════════════════════════════
    "/messages/send-poll": _with_options(
        "Creates and sends a poll to a WhatsApp chat. Recipients can vote on options.\n\n"
        "Required: `phone`, `name` (the poll question), `options` (array of strings, up to 12)."
    ),
    "/messages/send-poll-vote": _with_options(
        "Casts a vote on an existing poll.\n\n"
        "Required: `phone`, `options` (array of selected option strings), "
        "`pollId` (the poll message's ID)."
    ),

    # ═════════════════════════════════════════════════════════════════════
    # INTERACTIVE — ACTIONS (edit / delete / read)
    # ═════════════════════════════════════════════════════════════════════
    "/messages/edit": _with_options(
        "Edits an existing text message. Only works for messages sent by the same bot.\n\n"
        "Required: `phone`, `messageId`, `message` (new text content)."
    ),
    "/messages/delete":
        "Deletes a message for everyone (if possible, within WhatsApp's time limit) "
        "or just for the bot itself.\n\n"
        "Required: `phone`, `messageId`.",
    "/messages/read":
        "Marks one or more messages as read. Triggers the blue double-check "
        "for the sender.\n\n"
        "Required: `phone`, `messageIds` (array of message ID strings).",

    # ═════════════════════════════════════════════════════════════════════
    # AI
    # ═════════════════════════════════════════════════════════════════════
    "/ai/ask":
        "Sends a text message to Meta AI via WhatsApp and waits for a response.\n\n"
        "The message is forwarded to the Meta AI contact (13135550002@s.whatsapp.net). "
        "The server blocks until a reply is received or the `timeout` is reached.\n\n"
        "Required: `message` (your question/prompt).\n"
        "Optional: `timeout` (seconds to wait, default 30).\n\n"
        "Response includes:\n"
        "- `text` — the AI's textual reply\n"
        "- `hasImage` — whether the response contains an image\n"
        "- `messageId` — the WhatsApp message ID of the reply\n\n"
        "⚠ Requires an active WhatsApp connection.",
    "/ai/imagine":
        "Generates an image using Meta AI's `/imagine` feature.\n\n"
        "Internally sends `/imagine {prompt}` to Meta AI and returns "
        "the generated image (along with any accompanying text).\n\n"
        "Required: `prompt` — the image description.\n"
        "Optional: `timeout` (seconds to wait, default 60).\n\n"
        "Response shape is the same as /ai/ask, with `hasImage: true` when successful.\n\n"
        "⚠ Requires an active WhatsApp connection.",

    # ═════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═════════════════════════════════════════════════════════════════════
    "/settings/instance/call-reject-auto":
        "Enables or disables automatic call rejection. When enabled, incoming WhatsApp "
        "calls are automatically declined without ringing the paired device.\n\n"
        "Required: `value` (boolean).",
    "/settings/instance/call-reject-message":
        "Sets the message sent/displayed when a call is automatically rejected.\n\n"
        "Required: `value` (string). Only applies when `call-reject-auto` is enabled.",
    "/settings/instance/auto-read-message":
        "Enables or disables automatic read marking for incoming messages. "
        "When enabled, messages are marked as read immediately upon receipt.\n\n"
        "Required: `value` (boolean).",
    "/settings/ip-control":
        "Enables or disables IP-based access control. When enabled, only whitelisted "
        "IPs can reach the API. Requests from non-whitelisted IPs receive a 403.\n\n"
        "Required: `enabled` (boolean).",
    "/settings/ip-rules/whitelist":
        "Adds an IP address to the whitelist. Requires `ip-control` to be enabled.\n\n"
        "Required: `ip` (string, e.g. `\"192.168.1.100\"`).",
    "/settings/ip-rules/blacklist":
        "Adds an IP address to the blacklist. Requires `ip-control` to be enabled.\n\n"
        "Required: `ip` (string).",

    # ═════════════════════════════════════════════════════════════════════
    # INSTANCE / SESSION
    # ═════════════════════════════════════════════════════════════════════
    "/session/pair":
        "Pairs a new device using a pairing code — an alternative to QR code scanning.\n\n"
        "The server requests a pairing code from WhatsApp and displays it. "
        "Enter this code on the WhatsApp mobile app under Linked Devices.\n\n"
        "Required: `phone` (the phone number to pair, with country code).",
    "/instance/update-name":
        "Updates the display name of this API instance. The name appears in logs "
        "and status responses.\n\n"
        "Required: `name` (string).",

    # ═════════════════════════════════════════════════════════════════════
    # MANAGEMENT
    # ═════════════════════════════════════════════════════════════════════
    "/management/database/config":
        "Updates the database cleanup configuration.\n\n"
        "Required: `interval` — cleanup interval in minutes. Older messages "
        "are purged periodically based on this setting.",
    "/management/fetch_messages":
        "Fetches stored messages from the local database for a specific chat.\n\n"
        "Required: `phone` (the chat to fetch from).\n"
        "Optional: `limit` (max messages, default 20).",
    "/management/recent_contacts":
        "Returns the most recent contacts/chats the bot has interacted with.\n\n"
        "Optional: `limit` (max contacts, default 20).",

    # ═════════════════════════════════════════════════════════════════════
    # WEBHOOKS
    # ═════════════════════════════════════════════════════════════════════
    "/webhooks":
        "Creates a new webhook endpoint. The server will POST event payloads to "
        "this URL whenever matching events occur.\n\n"
        "Required: name, url, events (array of event names, or [\"*\"] for all), "
        "active (boolean to enable immediately).\n"
        "Optional: secret (string) — if set, outgoing payloads are signed with "
        "HMAC-SHA256 and the signature is sent in the X-Webhook-Signature header.\n\n"
        "Available event types:\n"
        "- `message.*` / `message.text` / `message.image` / `message.audio` / etc.\n"
        "- `message.contacts` — contact array messages\n"
        "- `message.sent` / `message.delivered` / `message.read` — delivery receipts\n"
        "- `message.poll_created` / `message.poll_vote` — poll events\n"
        "- `connection.*` — connection state changes\n"
        "- `qr.*` — QR code events\n"
        "- `call.*` — call events\n"
        "- `group.*` — group events\n"
        "- `contact.*` — presence/chat state events\n"
        "- `media.cleanup.*` — automatic media cleanup events\n"
        "- `ai.response` — Meta AI reply received",
    "/webhooks/{name}":
        "Updates an existing webhook by name. All fields are optional — send only "
        "what you want to change.\n\n"
        "Fields: url, method, headers, body, events, active, secret.\n"
        "If secret is set/changed, outgoing payloads will be signed with HMAC-SHA256.",
    "/webhooks/{name}/test":
        "Sends a test payload to a registered webhook to verify connectivity and "
        "payload format.\n\n"
        "The `{name}` path param specifies which webhook to test.\n\n"
        "Optional body — specify an `event` to choose which payload template to send. "
        "If omitted, defaults to `message.text`.\n\n"
        "Available event types for testing:\n"
        "- `message.text`, `message.image`, `message.video`, `message.audio`\n"
        "- `message.document`, `message.sticker`, `message.reaction`\n"
        "- `message.location`, `message.button_reply`, `message.list_reply`\n"
        "- `message.deleted`, `message.poll_created`, `message.poll_vote`\n"
        "- `message.sent`, `message.delivered`, `message.read`\n"
        "- `connection.connected`, `connection.disconnected`, `connection.qr_ready`\n"
        "- `group.join`, `contact.presence`, `contact.chat_presence`\n"
        "- `call.received`, `media.cleanup.completed`, `ai.response`\n\n"
        "Example body: `{\"event\": \"message.image\"}`\n\n"
        "Response includes the target's HTTP `statusCode` and `response` body.",

    # ═════════════════════════════════════════════════════════════════════
    # EXPORT / IMPORT
    # ═════════════════════════════════════════════════════════════════════
    "/management/export":
        "Exports all configuration data as a downloadable JSON file.\n\n"
        "Dumps all webhooks, instance settings, privacy settings, and IP rules "
        "into a single JSON export. Use /management/import to restore later.\n\n"
        "Response example:\n"
        '`{"success": true, "filename": "config_export_2026-06-08.json", '
        '"exported_at": "2026-06-08T23:19:00", '
        '"data": {"webhooks": [...], "settings": {...}, "ip_rules": {...}}}`',
    "/management/import":
        "Imports configuration data from a JSON file previously exported via "
        "/management/export.\n\n"
        "Accepts a multipart file upload. The file must be a valid JSON export "
        "(the same format produced by /management/export).\n\n"
        "All webhooks, settings, and IP rules in the file will be upserted "
        "(created if new, updated if existing).\n\n"
        "Required: `file` — the JSON export file to upload.\n\n"
        "Response: `{\"success\": true, \"imported\": {\"webhooks\": N, \"settings\": N, \"ipRules\": N}}`",

    # ═════════════════════════════════════════════════════════════════════
    # SYSTEM
    # ═════════════════════════════════════════════════════════════════════
    "/system/env":
        "Updates environment variables at runtime. Changes take effect immediately "
        "without requiring a server restart.\n\n"
        "Required: key-value pairs of env vars to set, e.g. `{\"PORT\": \"8300\"}`.",
}


def auto_generate_description(
    method: str,
    path: str,
    summary: str,
    operation: dict,
) -> str:
    """Generate a sensible description for any endpoint that lacks a manual one.

    Uses OpenAPI metadata (summary, description, parameter names, request body)
    to build a concise English description with optional field details.
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

    # Request body — required fields
    if body:
        content = body.get("content", {})
        for media_type, media_obj in content.items():
            schema = media_obj.get("schema", {})
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                readable = ref_name.replace("Request", "").replace("_", " ").strip()
                param_details.append(f"Request body: `{readable}` schema")
                break
            props = schema.get("properties", {})
            if props:
                required = set(schema.get("required", []))
                req_fields = [f"`{f}`" for f in props if f in required]
                opt_fields = [f"`{f}`" for f in props if f not in required and f not in ("reply", "type", "quoted_id", "delay_message", "delay_typing", "mentioned")]
                if req_fields:
                    param_details.append("Required: " + ", ".join(req_fields[:6]))
                if opt_fields:
                    param_details.append("Optional: " + ", ".join(opt_fields[:6]))
                    if len(opt_fields) > 6:
                        param_details[-1] += f" and {len(opt_fields) - 6} more"

    if param_details:
        parts.append("\n\n" + "\n".join(param_details))

    # Append note about common optional fields if the schema has "phone"
    if body:
        content = body.get("content", {})
        for media_obj in content.values():
            schema = media_obj.get("schema", {})
            props = schema.get("properties", {})
            if "phone" in props and ("reply" in props or "delay_message" in props):
                parts.append(
                    "\n\nCommon optional fields (see other message endpoints for details): "
                    "`delay_message`, `delay_typing`, `mentioned`, "
                    "`reply` (by text), `quoted_id` (by ID), `type` (`\"text\"` default or `\"id\"`)."
                )
                break

    description = operation.get("description", "")
    if description and description != summary:
        parts.append(f"\n\n{description}")

    return "".join(parts)
