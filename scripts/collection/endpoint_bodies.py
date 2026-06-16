"""Endpoint-specific request body overrides and field example values.

ENDPOINT_BODIES provides realistic example payloads for each route.
Uses special keys:
  - __formdata__: True → render as multipart/form-data instead of JSON
  - __file_field__: name of the file upload field (default: "file")
  - __commented__: dict of optional fields to show as // comments in JSON body
"""

from typing import Any, Dict, List, Set

# ── Known field mappings for better examples ────────────────────────────
FIELD_EXAMPLES: Dict[str, Any] = {
    "phone": "{{PHONE}}",
    "url": "https://example.com",
    "callPhone": "+5511999999999",
    "contactPhone": "5511999999999",
    "messageId": "MESSAGE_ID",
    "emoji": "👍",
    "pixKey": "yourkey@email.com",
    "merchantName": "My Store",
    "pixCity": "Sao Paulo",
    "pixDescription": "Order #1234",
    "name": "string",
    "message": "Hello! This is a test message.",
    "code": "123456",
    "caption": "Image caption",
    "fileName": "document.pdf",
    "lat": -23.550520,
    "lng": -46.633308,
    "pixValue": 19.90,
    "prompt": "A cute cat wearing a hat, digital art",
    "timeout": 30,
}

# ── Commented (optional) field templates ─────────────────────────────────
# Values = string representation that goes after `// "key": `
# The `|` separates example value from description of alternatives.

# For JSON endpoints with BaseWhatsAppRequest (type default = "text")
_COMMENTED_BASE = {
    "type": '"text", | text or id',
    "delay_message": "null,",
    "delay_typing": "null,",
    "mentioned": "null,",
    "quoted_id": "null,",
}

# For /messages/delete and /messages/read (type default = "id")
_COMMENTED_ID = {
    "type": '"id", | id (default)',
    "delay_message": "null,",
    "delay_typing": "null,",
    "mentioned": "null,",
    "quoted_id": "null,",
}

# For /send_bulk (no reply/quoted_id/type)
_COMMENTED_BULK = {
    "delay_message": "null,",
    "delay_typing": "null,",
    "mentioned": "null,",
    "delay_between": '"1-3", | number or range like "2-5"',
}

# For /send_reaction (extra fields)
_COMMENTED_REACTION = {
    "type": '"text", | text or id',
    "delay_message": "null,",
    "delay_typing": "null,",
    "mentioned": "null,",
    "quoted_id": "null,",
    "reaction": "null,",
    "text": "null,",
}


def _json_body(req: Dict[str, Any], *, commented: Dict[str, str] | None = None) -> Dict[str, Any]:
    """Build JSON body with active required fields + __commented__ optionals.

    Args:
        req: Required (active) fields with example values.
        commented: Optional fields dict. If omitted, uses _COMMENTED_BASE.
                   Key = field name, Value = string after `// "key": `.
    Returns:
        Dict with __commented__ + required fields.
    """
    return {
        "__commented__": commented or dict(_COMMENTED_BASE),
        **req,
    }


def _form_body(req: Dict[str, Any], extra_opts: Set[str] | None = None) -> Dict[str, Any]:
    """Build a multipart/form-data body with required fields + disabled optionals."""
    opts = {k: "" for k in ("delay_message", "delay_typing", "mentioned", "reply", "quoted_id")}
    if extra_opts:
        for k in extra_opts:
            opts[k] = ""
    result = {**opts, **req}
    result["__formdata__"] = True
    result["__file_field__"] = "file"
    return result


# ── Endpoint-specific body overrides ─────────────────────────────────────
# Key = URL path (without method — method is inferred from OpenAPI).
ENDPOINT_BODIES: Dict[str, Any] = {

    # ═══════════════════════════════════════════════════════════════════
    # TEXT
    # ═══════════════════════════════════════════════════════════════════
    "/send": _json_body({
        "phone": "{{PHONE}}",
        "message": "Hello! This is a test message.",
    }),
    "/send_bulk": {
        "__commented__": dict(_COMMENTED_BULK),
        "phones": ["{{PHONE}}", "5511988888888"],
        "message": "Hello! This is a bulk test message.",
    },
    "/send_reaction": {
        "__commented__": dict(_COMMENTED_REACTION),
        "__inline_comments__": {"messageId": "// or exact text"},
        "phone": "{{PHONE}}",
        "messageId": "MESSAGE_ID",
        "emoji": "👍",
    },

    # ═══════════════════════════════════════════════════════════════════
    # MEDIA (multipart/form-data) — uses disabled fields, not // comments
    # ═══════════════════════════════════════════════════════════════════
    "/send_image": _form_body({
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "Image caption",
        "as_document": False,
    }),
    "/send_audio": _form_body({
        "phone": "{{PHONE}}",
        "url": "",
        "ptt": False,
        "as_document": False,
        "format": "m4a",
    }),
    "/send_video": _form_body({
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "Video caption",
        "as_document": False,
    }),
    "/send_document": _form_body({
        "phone": "{{PHONE}}",
        "url": "",
        "fileName": "document.pdf",
        "caption": "Document caption",
    }),
    "/send_sticker": _form_body({
        "phone": "{{PHONE}}",
        "url": "https://www.gstatic.com/webp/gallery/1.webp",
        "pack": "Sticker Pack",
        "author": "Author Name",
        "resize_mode": "pad",
        "pad_color": "black",
        "blur_intensity": 20,
    }),
    "/send_gif": _form_body({
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "GIF caption",
    }),

    # ═══════════════════════════════════════════════════════════════════
    # LOCATION / CONTACT / LINK
    # ═══════════════════════════════════════════════════════════════════
    "/send_location": _json_body({
        "phone": "{{PHONE}}",
        "lat": -23.550520,
        "lng": -46.633308,
        "name": "Central Square",
        "address": "Sao Paulo, Brazil",
    }),
    "/send_contact": _json_body({
        "phone": "{{PHONE}}",
        "contactName": "John Doe",
        "contactPhone": "5511999999999",
    }),
    "/send_contacts": _json_body({
        "phone": "{{PHONE}}",
        "contacts": [
            {"name": "John Doe", "phone": "5511988888888"},
            {"name": "Jane Smith", "phone": "5511977777777"},
        ],
    }),
    "/send_link": _json_body({
        "phone": "{{PHONE}}",
        "url": "https://github.com",
        "message": "Check this out!",
        "title": "GitHub",
        "description": "Where the world builds software",
        "imageUrl": "https://example.com/image.png",
    }),

    # ═══════════════════════════════════════════════════════════════════
    # BUTTONS
    # ═══════════════════════════════════════════════════════════════════
    "/messages/send-button-list": _json_body({
        "phone": "{{PHONE}}",
        "message": "Choose an option:",
        "title": "Menu",
        "text": "What would you like to do?",
        "footer": "Tap a button below",
        "buttons": [
            {"type": "quick_reply", "buttonText": "Yes", "id": "yes"},
            {"type": "quick_reply", "buttonText": "No", "id": "no"},
            {"type": "url", "buttonText": "Visit Site", "url": "https://zapunlocked.com"},
            {"type": "call", "buttonText": "Call Support", "callPhone": "+5511999999999"},
            {"type": "otp", "buttonText": "Copy Code", "code": "591823"},
        ],
    }),
    "/messages/send-button-url": _json_body({
        "phone": "{{PHONE}}",
        "url": "https://zapunlocked.com",
        "button_text": "Visit Website",
        "title": "Get in touch",
        "text": "Visit our website:",
    }),
    "/messages/send-button-call": _json_body({
        "phone": "{{PHONE}}",
        "callPhone": "+5511999999999",
        "button_text": "Call Now",
        "title": "Contact us",
        "text": "Call us now:",
    }),
    "/messages/send-button-otp": _json_body({
        "phone": "{{PHONE}}",
        "code": "591823",
        "button_text": "Copy Code",
        "title": "Security Verification",
        "text": "Your access code is: 591823",
        "footer": "Valid for 5 minutes.",
    }),
    "/messages/send-button-pix": _json_body({
        "phone": "{{PHONE}}",
        "pixKey": "yourkey@email.com",
        "pixType": "EMAIL",
        "pixValue": 19.90,
        "merchantName": "My Store",
        "pixCity": "Sao Paulo",
        "pixDescription": "Order #1234",
        "button_text": "Pay",
        "title": "PIX Payment",
        "text": "Use the button below to pay via PIX:",
    }),
    "/messages/send-button-quick-reply": _json_body({
        "phone": "{{PHONE}}",
        "title": "Confirm",
        "text": "Do you agree?",
        "buttons": [
            {"text": "Yes", "id": "yes"},
            {"text": "No", "id": "no"},
        ],
    }),

    # ═══════════════════════════════════════════════════════════════════
    # OPTION LIST
    # ═══════════════════════════════════════════════════════════════════
    "/messages/send-option-list": _json_body({
        "phone": "{{PHONE}}",
        "title": "Choose an option",
        "text": "Please select:",
        "options": [
            {"title": "Option 1", "description": "First option"},
            {"title": "Option 2", "description": "Second option"},
        ],
        "button_text": "See options",
        "footer": "Footer text",
        "description": "Description text",
    }),

    # ═══════════════════════════════════════════════════════════════════
    # POLL
    # ═══════════════════════════════════════════════════════════════════
    "/messages/send-poll": _json_body({
        "phone": "{{PHONE}}",
        "name": "What is your favorite color?",
        "options": ["Red", "Blue", "Green", "Yellow"],
    }),
    "/messages/send-poll-vote": _json_body({
        "phone": "{{PHONE}}",
        "options": ["Blue"],
        "pollId": "POLL_ID",
    }),

    # ═══════════════════════════════════════════════════════════════════
    # ACTIONS (edit / delete / read)
    # ═══════════════════════════════════════════════════════════════════
    "/messages/delete": {
        "__commented__": dict(_COMMENTED_ID),
        "__inline_comments__": {"messageId": "// or exact text"},
        "phone": "{{PHONE}}",
        "messageId": "MESSAGE_ID",
    },
    "/messages/read": {
        "__commented__": dict(_COMMENTED_ID),
        "phone": "{{PHONE}}",
        "messageIds": ["FIRST_MSG_ID", "SECOND_MSG_ID"],
    },
    "/messages/edit": {
        "__commented__": dict(_COMMENTED_BASE),
        "__inline_comments__": {"messageId": "// or exact text"},
        "phone": "{{PHONE}}",
        "messageId": "MESSAGE_ID",
        "message": "Edited content here!",
    },

    # ═══════════════════════════════════════════════════════════════════
    # CONTACTS / SESSION (no commented optionals needed)
    # ═══════════════════════════════════════════════════════════════════
    "/contacts/info": {"phone": "{{PHONE}}"},
    "/settings/block": {"phone": "{{PHONE}}"},
    "/session/pair": {"phone": "{{PHONE}}"},
    "/session/logout": {},

    # ═══════════════════════════════════════════════════════════════════
    # SETTINGS / INSTANCE
    # ═══════════════════════════════════════════════════════════════════
    "/settings/profile": {
        "name": "My Bot",
        "about": "Powered by ZapUnlocked",
    },
    "/settings/instance/call-reject-auto": {"value": True},
    "/settings/instance/call-reject-message": {"value": "I can't answer right now."},
    "/settings/instance/auto-read-message": {"value": True},
    "/settings/ip-control": {"enabled": True},
    "/settings/ip-rules/whitelist": {"ip": "192.168.1.100"},
    "/settings/ip-rules/blacklist": {"ip": "10.0.0.50"},
    "/instance/update-name": {"name": "New Instance"},

    # ═══════════════════════════════════════════════════════════════════
    # MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════
    "/management/fetch_messages": {
        "phone": "{{PHONE}}",
        "limit": 20,
    },
    "/management/recent_contacts": {"limit": 20},
    "/management/database/config": {"interval": 1440},

    # ═══════════════════════════════════════════════════════════════════
    # EXPORT / IMPORT
    # ═══════════════════════════════════════════════════════════════════
    "/management/import": {
        "__formdata__": True,
        "__file_field__": "file",
        "file": "",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    "/system/env": {"PORT": "8300"},
    "/system/cleanup/settings": {"interval": 1440},

    # ═══════════════════════════════════════════════════════════════════
    # WEBHOOK
    # ═══════════════════════════════════════════════════════════════════
    "/webhooks": {
        "__commented__": {
            "secret": '"your-secret", | signs payload with HMAC-SHA256',
            "method": '"GET", | default: POST',
            "headers": '{"Authorization": "Bearer ..."}, | custom headers',
            "body": '{"key": "value"}, | request template body',
        },
        "name": "my-webhook",
        "url": "https://example.com/webhook",
        "events": ["*"],
        "active": True,
    },
    "/webhooks/{name}": {
        "__commented__": {
            "method": '"GET", | default: POST',
            "headers": '{"Authorization": "Bearer ..."}, | custom headers',
            "body": '{"key": "value"}, | request template body',
            "events": '["*"], | default: same as current',
            "active": "true, | toggle on/off",
            "secret": '"your-secret", | enable HMAC signing',
        },
        "url": "https://example.com/webhook",
    },

    # ═══════════════════════════════════════════════════════════════════
    # SESSIONS
    # ═══════════════════════════════════════════════════════════════════
    "/sessions": {
        "__commented__": {
            "name": '"My Session", | auto-generates if omitted',
        },
    },
    "/sessions/{session_id}/rename": {
        "name": "Renamed Session",
    },

    # ═══════════════════════════════════════════════════════════════════
    # AI
    # ═══════════════════════════════════════════════════════════════════
    "/ai/ask": {
        "message": "What is the capital of Brazil?",
        "timeout": 30,
    },
    "/ai/imagine": {
        "prompt": "A cute cat wearing a hat, digital art",
        "timeout": 60,
    },
}
