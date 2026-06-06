#!/usr/bin/env python3
"""
Auto-generate Postman collection from FastAPI OpenAPI schema.

Usage:
    python scripts/generate_collection.py

Generates: ZapUnlocked.collection.json (Postman v2.1 format)

How it works:
    1. Imports the FastAPI app (calls bootstrap() first)
    2. Gets the OpenAPI schema via app.openapi()
    3. Parses all paths, methods, parameters, request bodies
    4. Groups by URL prefix (e.g., /settings/privacy → Settings > Privacy)
    5. Generates example JSON bodies from schema types
    6. Saves to ZapUnlocked.collection.json

Run this script after adding/modifying any route to keep the collection in sync.
"""

import json
import os
import re
import sys
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Project root ─────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "ZapUnlocked.collection.json"

# ── Fix Windows console encoding for Unicode ─────────────────────────────
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── UI Style (matching scripts/lib/common.sh / common.ps1) ──────────────
_PURPLE = "\033[38;2;139;61;255m"
_GREEN  = "\033[38;2;66;194;146m"
_YELLOW = "\033[38;2;245;158;11m"
_RED    = "\033[38;2;239;68;68m"
_GRAY   = "\033[38;2;107;114;128m"
_WHITE  = "\033[38;2;233;213;255m"
_RESET  = "\033[0m"

_START_TIME = time.time()

def _elapsed() -> str:
    diff = time.time() - _START_TIME
    mins = int(diff // 60)
    secs = int(diff % 60)
    return f"{mins}m{secs}s" if mins else f"{secs}s"

def ui_banner():
    """Print ZapUnlocked ASCII banner (purple)."""
    print("")
    for line in [
        r"███████╗ █████╗ ██████╗ ██╗   ██╗███╗   ██╗██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗        █████╗ ██████╗ ██╗",
        r"╚══███╔╝██╔══██╗██╔══██╗██║   ██║████╗  ██║██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗      ██╔══██╗██╔══██╗██║",
        r"  ███╔╝ ███████║██████╔╝██║   ██║██╔██╗ ██║██║     ██║   ██║██║     █████╔╝ █████╗  ██║  ██║█████╗███████║██████╔╝██║",
        r" ███╔╝  ██╔══██║██╔═══╝ ██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██║  ██║╚════╝██╔══██║██╔═══╝ ██║",
        r"███████╗██║  ██║██║     ╚██████╔╝██║ ╚████║███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██████╔╝      ██║  ██║██║     ██║",
        r"╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝       ╚═╝  ╚═╝╚═╝     ╚═╝",
    ]:
        print(f"{_PURPLE}{line}{_RESET}")
    print("")

def ui_tags(icon: str, label: str, os_label: str = ""):
    """Print PY version + task tags (like common.sh ui_tags)."""
    py_ver = f"sys.version_info[:2]"
    import sys as _sys
    py = f"{_sys.version_info.major}.{_sys.version_info.minor}"
    tag_py  = f"{_PURPLE}[{_RESET}PY {py}{_PURPLE}]{_RESET}"
    tag_icon = f"{_PURPLE}[{_RESET}{icon} {label}{_PURPLE}]{_RESET}"
    parts = [tag_py, "  ", tag_icon]
    if os_label:
        parts += ["  ", f"{_PURPLE}[{_RESET}{os_label}{_PURPLE}]{_RESET}"]
    print("".join(parts))

def ui_sep():
    """Print a separator line."""
    print(f"{_GRAY}{'─' * 68}{_RESET}")

def ui_task(label: str):
    """Print a task section header."""
    print("")
    print(f"{_WHITE}  {label}{_RESET}")

def ui_info(msg: str):  print(f"  {_PURPLE}◉{_RESET} {msg}")
def ui_ok(msg: str):    print(f"  {_GREEN}✓{_RESET} {msg}")
def ui_warn(msg: str):  print(f"  {_YELLOW}⚠{_RESET} {msg}")
def ui_err(msg: str):   print(f"  {_RED}✖{_RESET} {msg}")
def ui_step(msg: str):  print(f"  {_GRAY}·{_RESET} {msg}")

def ui_footer(msg: str):
    """Print a footer with elapsed time."""
    print("")
    print(f"{_GREEN}✓{_RESET} {msg}  ({_elapsed()})")
    print("")

# ── Collection variables (Postman v2.1 / Insomnia) ─────────────────────
# Use {{VAR_NAME}} in requests (URL, headers, body).
# If a Postman GLOBAL variable with the same name exists, it overrides this one.
# Leave blank ("") to always prompt or rely on a global/secret store.
COLLECTION_VARS = [
    {"key": "BASE_URL",      "value": "http://localhost:8300",  "type": "default"},
    {"key": "API_KEY",       "value": "",                        "type": "secret"},
    {"key": "PHONE",         "value": "",                        "type": "default"},
    {"key": "WEBHOOK_NAME",  "value": "my-webhook",              "type": "default"},
    {"key": "IP",            "value": "192.168.1.100",           "type": "default"},
]

# ── Group definitions: path prefix → folder structure ────────────────────
#
# Each entry: (path_prefix, [folder, subfolder, ...])
# More specific (longer) prefixes win over shorter ones.
# "None" prefix = catch-all at root level.
#
# ── Naming convention ──────────────────────────────────────────────────
# - Top-level folders are capitalized: "Messages", "Settings", "Webhooks"
# - Subfolders reflect the URL hierarchy: /settings/privacy/about → Settings > Privacy
# - "Interactive Messages" is separate from plain "Messages"
# - Status has subfolders: General, Health, System
# - Instance has subfolders: Connection, Settings
# - Messages has subfolders: Text, Media > Upload, Location, Contact, Link, Reaction
#
FOLDER_MAP: List[Tuple[Optional[str], List[str]]] = [
    (None, ["Other"]),

    # ── Root / Collection ─────────────────────────────────────────────
    ("/collection.json", ["Collection"]),
    ("/", ["Status", "General"]),

    # ── Contacts ──────────────────────────────────────────────────────
    ("/contacts", ["Contacts"]),
    ("/settings/block", ["Contacts"]),

    # ── Instance ──────────────────────────────────────────────────────
    ("/instance/update-name", ["Instance"]),
    ("/instance/device",      ["Instance"]),
    ("/instance/me",          ["Instance"]),

    # ── Instance > Connection ─────────────────────────────────────────
    ("/qr",       ["Instance", "Connection"]),
    ("/session",  ["Instance", "Connection"]),

    # ── Instance > Settings ───────────────────────────────────────────
    ("/settings/instance",    ["Instance", "Settings"]),
    ("/settings/phone-code",  ["Instance", "Settings"]),

    # ── Messages (plain send) ─────────────────────────────────────────
    # Text
    ("/send",                   ["Messages", "Text"]),

    # Media
    ("/send_image",             ["Messages", "Media"]),
    ("/send_audio",             ["Messages", "Media"]),
    ("/send_video",             ["Messages", "Media"]),
    ("/send_document",          ["Messages", "Media"]),
    ("/send_sticker",           ["Messages", "Media"]),
    ("/send_gif",               ["Messages", "Media"]),
    # Media > Upload (reserved for when upload sub-routes are re-added)
    # ("/send_image/upload",    ["Messages", "Media", "Upload"]),
    # ("/send_audio/upload",    ["Messages", "Media", "Upload"]),
    # ("/send_video/upload",    ["Messages", "Media", "Upload"]),
    # ("/send_document/upload", ["Messages", "Media", "Upload"]),

    # Location
    ("/send_location",          ["Messages", "Location"]),

    # Contact
    ("/send_contact",           ["Messages", "Contact"]),
    ("/send_contacts",          ["Messages", "Contact"]),

    # Link
    ("/send_link",              ["Messages", "Link"]),

    # Reaction
    ("/send_reaction",          ["Messages", "Reaction"]),

    # ── Interactive Messages ──────────────────────────────────────────
    # Buttons
    ("/messages/send-button-list",         ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-url",          ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-call",         ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-otp",          ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-pix",          ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-quick-reply",  ["Interactive Messages", "Buttons"]),
    ("/messages/send-option-list",         ["Interactive Messages", "Buttons"]),

    # Poll
    ("/messages/send-poll",       ["Interactive Messages", "Poll"]),
    ("/messages/send-poll-vote",  ["Interactive Messages", "Poll"]),

    # Actions (edit / delete / read)
    ("/messages/delete",  ["Interactive Messages", "Actions"]),
    ("/messages/edit",    ["Interactive Messages", "Actions"]),
    ("/messages/read",    ["Interactive Messages", "Actions"]),

    # ── Management ────────────────────────────────────────────────────
    ("/management/database",        ["Management", "Database"]),
    ("/management/fetch_messages",  ["Management", "Messages"]),
    ("/management/recent_contacts", ["Management", "Messages"]),
    ("/management/cleanup",         ["Management", "Cleanup"]),

    # ── Settings ──────────────────────────────────────────────────────
    ("/settings/profile",    ["Settings", "Profile"]),
    ("/settings/privacy",    ["Settings", "Privacy"]),
    ("/settings/ip-control", ["Settings", "IP Control"]),
    ("/settings/ip-rules",   ["Settings", "IP Rules"]),

    # ── Status ────────────────────────────────────────────────────────
    # General (root, /status top, /logs)
    ("/status",         ["Status", "General"]),
    ("/logs",           ["Status", "General"]),
    # Health
    ("/status/health",   ["Status", "Health"]),
    ("/status/readiness",["Status", "Health"]),
    # System
    ("/status/memory",   ["Status", "System"]),
    ("/status/stream",   ["Status", "System"]),
    ("/status/volume",   ["Status", "System"]),

    # ── System ────────────────────────────────────────────────────────
    ("/system/env",          ["System", "Environment"]),
    ("/system/cleanup",      ["System", "Cleanup"]),

    # ── Webhooks ──────────────────────────────────────────────────────
    ("/webhooks", ["Webhooks"]),

    # ── AI ────────────────────────────────────────────────────────────
    ("/ai/ask",     ["AI"]),
    ("/ai/imagine", ["AI"]),
]


def resolve_ref(ref: str, schema: Dict) -> Dict:
    """Resolve a JSON Schema $ref to the actual schema definition."""
    parts = ref.lstrip("#/").split("/")
    current = schema
    for part in parts:
        if part in current:
            current = current[part]
        else:
            return {}
    return current


def get_schema_properties(schema_def: Dict, openapi_schema: Dict) -> Dict:
    """Get resolved properties from a schema definition, following $refs."""
    if "$ref" in schema_def:
        schema_def = resolve_ref(schema_def["$ref"], openapi_schema)
    if "allOf" in schema_def:
        combined = {}
        for sub in schema_def["allOf"]:
            combined.update(get_schema_properties(sub, openapi_schema))
        return combined
    return {k: v for k, v in schema_def.get("properties", {}).items()}


def get_required_fields(schema_def: Dict, openapi_schema: Dict) -> List[str]:
    """Get required fields from a schema definition."""
    if "$ref" in schema_def:
        schema_def = resolve_ref(schema_def["$ref"], openapi_schema)
    if "allOf" in schema_def:
        required = []
        for sub in schema_def["allOf"]:
            required.extend(get_required_fields(sub, openapi_schema))
        return required
    return schema_def.get("required", [])


# ── Known field mappings for better examples ────────────────────────────
FIELD_EXAMPLES = {
    "phone": "{{PHONE}}",
    "url": "https://example.com",
    "image_url": "https://picsum.photos/800/600",
    "video_url": "https://test-videos.co.uk/vids/bigbuckbunny/mp4/av1/360/Big_Buck_Bunny_360_10s_1MB.mp4",
    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "document_url": "https://raw.githubusercontent.com/KAUAxiis/database/main/README.md",
    "sticker_url": "https://www.gstatic.com/webp/gallery/1.webp",
    "callPhone": "+5511999999999",
    "contactPhone": "5511999999999",
    "messageId": "ID_DA_MENSAGEM",
    "emoji": "\\uD83D\\uDC4D",
    "pixKey": "suachave@email.com",
    "merchantName": "Minha Loja",
    "pixCity": "Sao Paulo",
    "pixDescription": "Compra #1234",
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

# ── Endpoint-specific body overrides for better examples ─────────────────
ENDPOINT_BODIES = {
    "/send": {
        "phone": "{{PHONE}}",
        "message": "Hello! This is a test message.",
        "delay_message": None,
        "delay_typing": 2,
        "mentioned": None,
    },
    # ── Media (unified: url OR file upload) ──────────────────────────
    # These endpoints use multipart/form-data (Form + File),
    # NOT JSON. Use `url` field for URL-based sending or `file` for upload.
    "/send_image": {
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "Image caption",
        "as_document": False,
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_audio": {
        "phone": "{{PHONE}}",
        "url": "",
        "ptt": False,
        "as_document": False,
        "format": "m4a",
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_video": {
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "Video caption",
        "as_document": False,
        "gif_playback": False,
        "ptv": False,
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_document": {
        "phone": "{{PHONE}}",
        "url": "",
        "file_name": "document.pdf",
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_gif": {
        "phone": "{{PHONE}}",
        "url": "",
        "caption": "Funny gif",
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_sticker": {
        "phone": "{{PHONE}}",
        "url": "https://www.gstatic.com/webp/gallery/1.webp",
        "pack": "My Sticker Pack",
        "author": "ZapUnlocked",
        "resize_mode": "pad",
        "pad_color": "black",
        "blur_intensity": 20,
        "delay_message": "",
        "delay_typing": "",
        "mentioned": "",
        "__formdata__": True,
        "__file_field__": "file",
    },
    "/send_contact": {
        "phone": "{{PHONE}}",
        "name": "ZapUnlocked Support",
        "contactPhone": "5511999999999",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/send_contacts": {
        "phone": "{{PHONE}}",
        "contacts": [
            {"name": "John Doe", "phone": "5511988888888"},
            {"name": "Jane Smith", "phone": "5511977777777"},
        ],
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/send_link": {
        "phone": "{{PHONE}}",
        "url": "https://github.com",
        "text": "Check out this repository!",
        "title": "GitHub",
        "description": "Where the world builds software",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/send_location": {
        "phone": "{{PHONE}}",
        "lat": -23.550520,
        "lng": -46.633308,
        "name": "Central Square",
        "address": "New York, NY",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/send_reaction": {
        "phone": "{{PHONE}}",
        "messageId": "ID_DA_MENSAGEM",
        "emoji": "\\uD83D\\uDC4D",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/session/pair": {
        "phone": "{{PHONE}}",
    },
    "/messages/send-button-list": {
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
        "delay_message": "2-5",
        "delay_typing": 3,
        "mentioned": ["5511999999999"],
    },
    "/messages/send-button-quick-reply": {
        "phone": "{{PHONE}}",
        "title": "Confirm",
        "text": "Do you agree?",
        "buttons": [
            {"text": "Yes", "id": "yes"},
            {"text": "No", "id": "no"},
        ],
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/send-button-url": {
        "phone": "{{PHONE}}",
        "url": "https://zapunlocked.com",
        "button_text": "Visit Website",
        "title": "Get in touch",
        "text": "Visit our website:",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/send-button-call": {
        "phone": "{{PHONE}}",
        "callPhone": "+5511999999999",
        "button_text": "Call Now",
        "title": "Contact us",
        "text": "Call us now:",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/send-button-otp": {
        "phone": "{{PHONE}}",
        "code": "591823",
        "button_text": "Copy Code",
        "title": "Security Verification",
        "text": "Your access code is: 591823",
        "footer": "Valid for 5 minutes.",
        "delay_typing": 1.5,
    },
    "/messages/send-button-pix": {
        "phone": "{{PHONE}}",
        "pixKey": "suachave@email.com",
        "pixType": "EMAIL",
        "pixValue": 19.90,
        "merchantName": "Minha Loja",
        "pixCity": "Sao Paulo",
        "pixDescription": "Compra #1234",
        "button_text": "Pagar",
        "title": "PIX Payment",
        "text": "Use the button below to pay via PIX:",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/send-poll": {
        "phone": "{{PHONE}}",
        "name": "What is your favorite color?",
        "options": ["Red", "Blue", "Green", "Yellow"],
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/send-poll-vote": {
        "phone": "{{PHONE}}",
        "options": ["Blue"],
        "pollId": "ID_DA_ENQUETE",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/delete": {
        "phone": "{{PHONE}}",
        "messageId": "ID_DA_MENSAGEM",
    },
    "/messages/edit": {
        "phone": "{{PHONE}}",
        "messageId": "ID_DA_MENSAGEM",
        "message": "Edited content here!",
        "delay_message": None,
        "delay_typing": None,
        "mentioned": None,
    },
    "/messages/read": {
        "phone": "{{PHONE}}",
        "messageIds": ["ID_PRIMEIRA_MSG", "ID_SEGUNDA_MSG"],
    },
    "/contacts/info": {
        "phone": "{{PHONE}}",
    },
    "/settings/block": {
        "phone": "{{PHONE}}",
        "action": "block",
    },
    "/settings/profile": {
        "name": "My Bot",
        "newProfilePictureUrl": "https://picsum.photos/400/400",
    },
    "/settings/privacy/last-seen": {"value": "all"},
    "/settings/privacy/online": {"value": "all"},
    "/settings/privacy/profile": {"value": "contacts"},
    "/settings/privacy/status": {"value": "contacts"},
    "/settings/privacy/read-receipts": {"value": "all"},
    "/settings/privacy/groups-add": {"value": "contacts"},
    "/settings/privacy/call-add": {"value": "all"},
    "/settings/privacy/about": {"value": "Available via ZapUnlocked Bot"},
    "/settings/privacy/disappearing-timer": {"value": 24},
    "/settings/instance/call-reject-auto": {"value": True},
    "/settings/instance/call-reject-message": {"value": "I can't answer right now."},
    "/settings/instance/auto-read-message": {"value": True},
    "/settings/ip-control": {"enabled": True},
    "/settings/ip-rules/whitelist": {"ip": "192.168.1.100"},
    "/settings/ip-rules/blacklist": {"ip": "10.0.0.50"},
    "/instance/update-name": {"name": "New Instance"},
    "/management/fetch_messages": {
        "phone": "{{PHONE}}",
        "limit": 20,
    },
    "/management/recent_contacts": {"limit": 20},
    "/management/database/config": {"interval": 1440},
    "/system/env": {"PORT": "8300"},
    "/system/cleanup/settings": {"interval": 1440},
    "/webhooks": {
        "name": "my-webhook",
        "url": "https://myserver.com/hook",
        "events": ["*"],
        "active": True,
    },

    # ── AI ────────────────────────────────────────────────────────────
    "/ai/ask": {
        "message": "What is the capital of Brazil?",
        "timeout": 30,
    },
    "/ai/imagine": {
        "prompt": "A cute cat wearing a hat, digital art",
        "timeout": 60,
    },
}

# ── Fields to SKIP in generated examples (too verbose / rarely used) ─────
SKIP_FIELDS = {"reply", "quoted_id"}


def generate_example_value(prop: Dict, openapi_schema: Dict, depth: int = 0) -> Any:
    """Generate an example value from a JSON schema property."""
    if depth > 5:
        return None

    # Follow $ref
    if "$ref" in prop:
        resolved = resolve_ref(prop["$ref"], openapi_schema)
        if resolved:
            return generate_example_value(resolved, openapi_schema, depth + 1)
        return {}

    # Use explicit example if provided
    if "example" in prop:
        return prop["example"]

    # Use default if provided
    if "default" in prop:
        return prop["default"]

    prop_type = prop.get("type", "string")
    enum_vals = prop.get("enum")
    fmt = prop.get("format", "")

    if enum_vals:
        return enum_vals[0]

    if prop_type == "string":
        if fmt in ("uri", "url"):
            return "https://example.com"
        return "string"

    if prop_type == "integer":
        return 0

    if prop_type == "number":
        return 0.0

    if prop_type == "boolean":
        return False

    if prop_type == "array":
        items = prop.get("items", {})
        example_item = generate_example_value(items, openapi_schema, depth + 1)
        return [example_item] if example_item is not None else []

    if prop_type == "object":
        result = {}
        for key, val in prop.get("properties", {}).items():
            example = generate_example_value(val, openapi_schema, depth + 1)
            if example is not None:
                result[key] = example
        return result

    return None


def generate_request_body(request_body: Dict, openapi_schema: Dict) -> Optional[str]:
    """Generate an example JSON body from an OpenAPI requestBody definition."""
    if not request_body:
        return None

    content = request_body.get("content", {})
    if "application/json" not in content:
        return None

    media = content["application/json"]
    schema_def = media.get("schema", {})

    # Get properties and required fields
    properties = get_schema_properties(schema_def, openapi_schema)
    required = get_required_fields(schema_def, openapi_schema)

    if not properties:
        return None

    # Build example body
    body = OrderedDict()

    # Priority 1: required fields (with known examples if available)
    for field in required:
        if field in SKIP_FIELDS:
            continue
        if field in FIELD_EXAMPLES:
            body[field] = FIELD_EXAMPLES[field]
        elif field in properties:
            val = generate_example_value(properties[field], openapi_schema)
            if val is not None:
                body[field] = val

    # Priority 2: optional fields that have known examples
    for field in FIELD_EXAMPLES:
        if field not in body and field in properties and field not in SKIP_FIELDS:
            body[field] = FIELD_EXAMPLES[field]

    # Priority 3: other optional fields with defaults (useful ones)
    for field, prop in properties.items():
        if field not in body and field not in SKIP_FIELDS:
            if "default" in prop:
                body[field] = prop["default"]
            elif field == "button_text" and "default" in prop:
                body[field] = prop["default"]

    if not body:
        return None

    return json.dumps(body, indent=4, ensure_ascii=False)


def get_path_parameters(path: str, operation: Dict, openapi_schema: Dict) -> List[Dict]:
    """Extract URL path parameters and convert to Postman variables."""
    params = []
    for param in operation.get("parameters", []):
        if param.get("in") == "path":
            name = param["name"]
            # Convert {phone} to {{PHONE}} if known, otherwise {{name}}
            var_name = name.upper()
            if var_name in [v["key"] for v in COLLECTION_VARS]:
                params.append({"key": f"{{{{{var_name}}}}}", "value": "", "disabled": False})
            else:
                params.append({"key": name, "value": "", "disabled": False})
    return params


def build_collection(openapi_schema: Dict) -> Dict:
    """Build the Postman v2.1 collection from the OpenAPI schema."""
    paths = openapi_schema.get("paths", {})
    info = openapi_schema.get("info", {})

    collection: Dict = OrderedDict([
        ("info", OrderedDict([
            ("name", f"{info.get('title', 'API')} (auto-generated)"),
            ("schema", "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"),
            ("description", f"Auto-generated from OpenAPI. Base URL: http://localhost:{os.getenv('PORT', '8300')}"),
        ])),
        ("variable", COLLECTION_VARS),
        ("item", []),
    ])

    # ── Build folder tree ────────────────────────────────────────────────
    # folder_tree: { "folder_name": { "_items": [...], "sub": { ... } } }
    folder_tree: Dict = {}

    def ensure_folder(path_parts: List[str]) -> Dict:
        """Navigate/create folder tree and return the target dict."""
        current = folder_tree
        for part in path_parts:
            if part not in current:
                current[part] = {"_items": []}
            current = current[part]
        return current

    def find_folder(path: str) -> List[str]:
        """Find the best folder path for a given URL path."""
        # Try exact prefix match first, then longest prefix
        matches = []
        for prefix, folders in FOLDER_MAP:
            if prefix is None:
                continue
            if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "{"):
                matches.append((len(prefix), folders))

        if not matches:
            # Extract from path: /foo/bar/baz → ["Foo", "Bar"]
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            if parts:
                return [p.capitalize() for p in parts[:2]]
            return ["Other"]

        # Return longest prefix match
        matches.sort(key=lambda x: -x[0])
        return matches[0][1]

    # ── Process each path/operation ──────────────────────────────────────
    for url_path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            method = method.upper()
            if method not in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                continue

            summary = operation.get("summary", "") or url_path
            has_security = bool(operation.get("security"))

            # Build request URL (replace path params with Postman variables)
            postman_url = url_path
            postman_path_parts = []
            for segment in url_path.strip("/").split("/"):
                if segment.startswith("{") and segment.endswith("}"):
                    var_name = segment[1:-1].upper()
                    if var_name in [v["key"] for v in COLLECTION_VARS]:
                        postman_path_parts.append(f"{{{{{var_name}}}}}")
                    else:
                        postman_path_parts.append(f":{segment[1:-1]}")
                elif segment:
                    postman_path_parts.append(segment)

            raw_url = "{{BASE_URL}}/" + "/".join(postman_path_parts) if postman_path_parts else "{{BASE_URL}}/"

            # Headers
            headers = []
            if method in ("POST", "PUT"):
                headers.append({"key": "Content-Type", "value": "application/json"})
            if has_security:
                headers.append({"key": "x-api-key", "value": "{{API_KEY}}"})

            # Request body (use endpoint-specific override if available)
            body = None
            if url_path in ENDPOINT_BODIES:
                body_data = dict(ENDPOINT_BODIES[url_path])  # copy to avoid mutating original
                if body_data.pop("__formdata__", False):
                    # ── Multipart form-data ──────────────────────────────
                    file_field = body_data.pop("__file_field__", "file")
                    formdata = []
                    for key, val in body_data.items():
                        formdata.append({
                            "key": key,
                            "value": str(val).lower() if isinstance(val, bool) else str(val),
                            "type": "text",
                        })
                    formdata.insert(0, {
                        "key": file_field,
                        "value": "",
                        "type": "file",
                        "src": [],
                    })
                    body = {"mode": "formdata", "formdata": formdata}
                else:
                    body = {
                        "mode": "raw",
                        "raw": json.dumps(body_data, indent=4, ensure_ascii=False),
                        "options": {"raw": {"language": "json"}},
                    }
            elif "requestBody" in operation:
                # Check if multipart/form-data
                content_map = operation["requestBody"].get("content", {})
                if "multipart/form-data" in content_map:
                    form_fields = {"phone": "{{PHONE}}"}
                    props = content_map["multipart/form-data"].get("schema", {}).get("properties", {})
                    for key, prop in props.items():
                        if key == "file" or prop.get("format") == "binary":
                            continue
                        if "default" in prop:
                            form_fields[key] = prop["default"]
                    formdata = [{"key": k, "value": str(v), "type": "text"} for k, v in form_fields.items()]
                    formdata.insert(0, {"key": "file", "value": "", "type": "file", "src": []})
                    body = {"mode": "formdata", "formdata": formdata}
                else:
                    body_text = generate_request_body(operation["requestBody"], openapi_schema)
                    if body_text:
                        body = {
                            "mode": "raw",
                            "raw": body_text,
                            "options": {"raw": {"language": "json"}},
                        }

            # Build request dict
            request_item = OrderedDict([
                ("name", summary or url_path),
                ("request", OrderedDict([
                    ("method", method),
                    ("url", OrderedDict([
                        ("raw", raw_url),
                        ("host", ["{{BASE_URL}}"]),
                        ("path", postman_path_parts or [""]),
                    ])),
                ])),
            ])

            if headers:
                request_item["request"]["header"] = headers
            if body:
                request_item["request"]["body"] = body

            # ── Place in folder tree ─────────────────────────────────────
            folder_parts = find_folder(url_path)
            if folder_parts:
                parent = ensure_folder(folder_parts)
                parent["_items"].append(request_item)
            else:
                collection["item"].append(request_item)

    # ── Convert folder tree to Postman items ─────────────────────────────
    def build_items(tree: Dict) -> List[Dict]:
        """Convert folder tree dict to Postman item list."""
        items = []
        for name, content in sorted(tree.items()):
            if name == "_items":
                continue
            sub_items = list(content.get("_items", []))
            child_items = build_items(content)
            sub_items.extend(child_items)

            if sub_items:
                items.append(OrderedDict([
                    ("name", name),
                    ("item", sub_items),
                ]))
        return items

    collection["item"] = build_items(folder_tree)
    return collection


def main():
    """Main entry point."""
    ui_banner()
    ui_tags("▶", "COLLECTION GENERATOR", "Postman v2.1")
    ui_sep()

    # ── 1. Bootstrap environment ──────────────────────────────────────────
    ui_task("Bootstrapping environment")
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("MALLOC_ARENA_MAX", "1")
    from src.bootstrap import bootstrap
    bootstrap()
    ui_ok("Environment ready")

    # ── 2. Load app & OpenAPI schema ──────────────────────────────────────
    ui_task("Reading OpenAPI schema")
    from src.app import create_app
    app = create_app()
    openapi_schema = app.openapi()

    paths = openapi_schema.get("paths", {})
    total_ops = sum(len(methods) for methods in paths.values())
    ui_ok(f"Found {total_ops} operations across {len(paths)} paths")

    # ── 3. Build collection ───────────────────────────────────────────────
    ui_task("Building Postman collection")
    collection = build_collection(openapi_schema)

    def count_items(items) -> int:
        c = 0
        for item in items:
            if "item" in item:
                c += count_items(item["item"])
            else:
                c += 1
        return c

    total_items = count_items(collection["item"])
    ui_ok(f"{total_items} requests organized into {len(collection['item'])} folders")

    # ── 4. Save ───────────────────────────────────────────────────────────
    ui_task("Saving collection")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    ui_ok(f"Saved to {OUTPUT_FILE}")

    # ── 5. Print folder structure ─────────────────────────────────────────
    ui_task("Folder structure")
    def print_tree(items, indent=0):
        for item in items:
            if "item" in item:
                print(f"{'  ' * indent}{_PURPLE}[{item['name']}]{_RESET}")
                print_tree(item["item"], indent + 1)
            else:
                req = item.get("request", {})
                _c = _GREEN if req.get("method") == "GET" else _YELLOW if req.get("method") == "POST" else _GRAY
                print(f"{'  ' * indent}  {_c}{req.get('method', '?'):6s}{_RESET} {item['name']}")

    print_tree(collection["item"])

    ui_sep()
    ui_footer("Collection generated successfully")


if __name__ == "__main__":
    main()
