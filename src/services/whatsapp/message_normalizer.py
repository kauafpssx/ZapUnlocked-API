"""Canonical message normalizer — single source of truth for inbound events.

Converts a Neonize ``MessageEv`` into a canonical ``MessageEvent`` envelope so
that storage, the webhook router, and future automations all consume the same
normalized shape instead of re-reading protobufs independently.

Reference: ``NEONIZE_0.12.4_MAP/01_ARQUITETURA_E_CONVENCOES.md`` and
``NEONIZE_0.12.4_MAP/12_WEBHOOKS_E_PARSER.md``.

Design rules (see map doc 12):
- respect only fields that are present (``HasField``/default comparison);
- convert ``bytes`` to a safe placeholder (never dump raw material);
- limit recursion depth and collection size;
- redact tokens, media keys and cryptographic material;
- never raise on an unknown/new field.
"""

from __future__ import annotations

import json
from typing import Any

# ── Redaction ────────────────────────────────────────────────────────────────
# Substrings (lower-cased) that mark a dict key as sensitive. Kept narrow on
# purpose: a bare "key" must NOT be redacted (JID keys, row IDs, etc.).
_SENSITIVE_SUBSTRINGS = (
    "token",
    "media_key",
    "mediakey",
    "secret",
    "password",
    "privatekey",
    "private_key",
    "encryptionkey",
    "encryption_key",
    "apikey",
    "api_key",
)
REDACTED = "***REDACTED***"
_BYTES_PLACEHOLDER = "<bytes:{n}>"

_MAX_DEPTH = 8
_MAX_ITEMS = 300

# Detected protobuf field → default webhook event name.
_EVENT_BY_TYPE = {
    "conversation": "message.text",
    "extendedTextMessage": "message.text",
    "imageMessage": "message.image",
    "videoMessage": "message.video",
    "audioMessage": "message.audio",
    "documentMessage": "message.document",
    "stickerMessage": "message.sticker",
    "contactMessage": "message.contact",
    "contactsArrayMessage": "message.contacts",
    "locationMessage": "message.location",
    "reactionMessage": "message.reaction",
    "liveLocationMessage": "message.location",
    "pollCreationMessage": "message.poll_created",
    "pollCreationV2Message": "message.poll_created",
    "pollCreationV3Message": "message.poll_created",
    "pollUpdateMessage": "message.poll_vote",
    "pollUpdateMessageMetadata": "message.poll_vote",
    "interactiveResponseMessage": "message.native_flow_response",
    "orderMessage": "message.order_received",
    "productMessage": "message.product_received",
    "documentWithCaptionMessage": "message.document",
    "ptvMessage": "message.video",
}

# Message fields checked, in order, when detecting the type.
_TYPE_FIELDS = (
    "conversation",
    "extendedTextMessage",
    "imageMessage",
    "videoMessage",
    "ptvMessage",
    "audioMessage",
    "documentMessage",
    "documentWithCaptionMessage",
    "stickerMessage",
    "contactMessage",
    "contactsArrayMessage",
    "locationMessage",
    "liveLocationMessage",
    "reactionMessage",
    "pollCreationMessage",
    "pollCreationV2Message",
    "pollCreationV3Message",
    "pollUpdateMessage",
    "pollUpdateMessageMetadata",
    "interactiveResponseMessage",
    "orderMessage",
    "productMessage",
)

# Message fields that may carry a contextInfo (quoted/mentions).
_CONTEXT_FIELDS = (
    "extendedTextMessage",
    "imageMessage",
    "videoMessage",
    "ptvMessage",
    "audioMessage",
    "documentMessage",
    "stickerMessage",
    "locationMessage",
    "contactMessage",
    "interactiveResponseMessage",
    "orderMessage",
    "productMessage",
)


# ── Low-level safe access ────────────────────────────────────────────────────

def _get(obj: Any, name: str, default: Any = None) -> Any:
    """Safe attribute read that never raises (works on protobuf and mocks)."""
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def _is_set(obj: Any, field: str) -> bool:
    """Return True when a protobuf field is present/non-default, never raises."""
    if obj is None:
        return False
    try:
        val = getattr(obj, field)
    except Exception:
        return False
    if val is None:
        return False
    try:
        # For message fields this is cheap; for scalars compare against default.
        return val != type(val)()
    except Exception:
        return bool(val)


def detect_type(raw: Any) -> str:
    """Return the name of the set Message field, or ``'unknown'``."""
    if raw is None:
        return "unknown"
    for field in _TYPE_FIELDS:
        if _is_set(raw, field):
            return field
    return "unknown"


# ── JID / PN-LID resolution (single source) ──────────────────────────────────

def resolve_chat_jid(source: Any, fallback_phone: str = "") -> str:
    """Resolve the canonical chat JID from a message source (PN/LID aware).

    Groups keep ``@g.us``; bot-server chats return the bare identifier; ``lid``
    chats are mapped to the real ``@s.whatsapp.net`` number when available,
    otherwise fall back to the raw chat id.
    """
    chat = _get(source, "Chat")
    is_group = bool(_get(source, "IsGroup", False))
    chat_user = _safe_user(chat)

    if is_group:
        return f"{chat_user}@g.us" if chat_user else fallback_phone

    chat_server = _safe_server(chat)

    if chat_server == "bot":
        return chat_user or fallback_phone

    if chat_server == "lid":
        for attr in ("SenderAlt", "RecipientAlt", "Sender"):
            alt = _get(source, attr)
            alt_user = _safe_user(alt)
            alt_server = _safe_server(alt)
            if alt_user and alt_server == "s.whatsapp.net":
                return f"{alt_user}@s.whatsapp.net"

    if chat_user:
        return f"{chat_user}@s.whatsapp.net"
    return fallback_phone


def _safe_user(jid: Any) -> str:
    try:
        return str(_get(jid, "User", "") or "")
    except Exception:
        return ""


def _safe_server(jid: Any) -> str:
    try:
        return str(_get(jid, "Server", "") or "")
    except Exception:
        return ""


def normalize_sender_jid(source: Any, chat_jid: str, fallback_phone: str = "") -> str:
    """Best-effort resolution of the actual sender JID for a message."""
    sender = _get(source, "Sender")
    sender_user = _safe_user(sender)
    sender_server = _safe_server(sender)
    if sender_user and sender_server:
        return f"{sender_user}@{sender_server}"
    # LID chats: SenderAlt may hold the real number.
    sender_alt = _get(source, "SenderAlt")
    alt_user = _safe_user(sender_alt)
    alt_server = _safe_server(sender_alt)
    if alt_user and alt_server == "s.whatsapp.net":
        return f"{alt_user}@{alt_server}"
    return chat_jid or fallback_phone


# ── Key / context ────────────────────────────────────────────────────────────

def normalize_message_key(info: Any, fallback_phone: str = "") -> dict:
    """Normalize the message key (id, chat, sender, timestamp, flags)."""
    source = _get(info, "MessageSource")
    chat_jid = resolve_chat_jid(source, fallback_phone)
    return {
        "id": _safe_str(_get(info, "ID")),
        "fromMe": bool(_get(source, "IsFromMe", False)),
        "isGroup": bool(_get(source, "IsGroup", False)),
        "pushname": _safe_str(_get(info, "Pushname")),
        "timestamp": _safe_int(_get(info, "Timestamp")),
        "chatJid": chat_jid,
        "senderJid": normalize_sender_jid(source, chat_jid, fallback_phone),
        "server": _safe_server(_get(source, "Chat")),
        "category": _safe_str(_get(info, "Category")),
    }


def normalize_context(raw: Any) -> dict:
    """Extract quoted-message id and mentioned JIDs from any message type."""
    result = {"quotedMessageId": None, "quotedParticipant": None, "mentionedJids": []}
    for field in _CONTEXT_FIELDS:
        if not _is_set(raw, field):
            continue
        try:
            ctx = getattr(getattr(raw, field), "contextInfo", None)
        except Exception:
            ctx = None
        ctx = _extract_context_info(ctx)
        if ctx:
            result.update(ctx)
            break
    return result


def _extract_context_info(ctx: Any) -> dict | None:
    if ctx is None:
        return None
    stanza = _safe_str(_get(ctx, "stanzaID"))
    participant = _safe_str(_get(ctx, "participant"))
    mentioned: list[str] = []
    for field in ("mentionedJID", "mentionedJid"):
        try:
            for jid in _get(ctx, field, []) or []:
                val = _safe_str(_get(jid, "User")) or _safe_str(jid)
                if val:
                    mentioned.append(val)
        except Exception:
            pass
        if mentioned:
            break
    if not stanza and not mentioned:
        return None
    return {
        "quotedMessageId": stanza or None,
        "quotedParticipant": participant or None,
        "mentionedJids": mentioned,
    }


# ── Native Flow / interactive responses ──────────────────────────────────────

_FORM_FLOW_NAME = "galaxy_message"
_LIST_FLOW_NAMES = {"single_select", "single_select_multiple"}
_BUTTON_FLOW_NAMES = {
    "quick_reply",
    "cta_url",
    "cta_call",
    "cta_copy",
    "reminder",
    "cancel_reminder",
    "address_message",
    "location_request_message",
    "review_and_pay",
    "payment_info",
    "wa_payment",
}


def normalize_native_flow_response(resp: Any) -> dict:
    """Normalize an ``InteractiveResponseMessage`` preserving the full payload.

    Returns ``name``, ``version``, parsed ``params`` (or ``None`` on error),
    the original ``paramsJSON`` string, an optional ``parseError`` and a
    ``kind`` in ``{"form", "list", "button", "unknown"}``. ``kind`` replaces
    the old (unreliable) ``id.isdigit()`` heuristic.
    """
    native = _get(resp, "nativeFlowResponseMessage")
    name = _safe_str(_get(native, "name"))
    version = _safe_int(_get(native, "version"))
    raw_json = _safe_str(_get(native, "paramsJSON"))

    params: dict | None = None
    parse_error: str | None = None
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            params = parsed if isinstance(parsed, dict) else {"value": parsed}
        except (ValueError, TypeError) as exc:
            parse_error = str(exc)

    source_message_id = _extract_context_info(_get(resp, "contextInfo")) or {}
    source_id = source_message_id.get("quotedMessageId")

    kind = _classify_native_flow(name, params)

    return {
        "name": name,
        "version": version,
        "params": params,
        "rawParamsJSON": raw_json,
        "parseError": parse_error,
        "kind": kind,
        "sourceMessageId": source_id,
    }


def _classify_native_flow(name: str, params: dict | None) -> str:
    """Classify a native-flow response into form/list/button/unknown."""
    lname = name.lower()
    if lname == _FORM_FLOW_NAME:
        return "form"
    if params:
        if "sections" in params or "rows" in params:
            return "list"
    if lname in _LIST_FLOW_NAMES:
        return "list"
    if lname in _BUTTON_FLOW_NAMES:
        return "button"
    # Params carrying an id/display_text but no list structure → quick reply.
    if params and ("id" in params or "display_text" in params or "title" in params):
        return "button"
    return "unknown"


# ── Orders / products ────────────────────────────────────────────────────────

def normalize_order(order_msg: Any) -> dict:
    """Normalize an ``OrderMessage`` (header only — items come from the API)."""
    status_int = _safe_int(_get(order_msg, "status"))
    return {
        "orderId": _safe_str(_get(order_msg, "orderID")),
        "requestMessageId": _safe_str(_get(order_msg, "orderRequestMessageID")),
        "itemCount": _safe_int(_get(order_msg, "itemCount")),
        "status": status_int,
        "statusName": _enum_name(order_msg, "status"),
        "surface": _enum_name(order_msg, "surface"),
        "message": _safe_str(_get(order_msg, "message")),
        "title": _safe_str(_get(order_msg, "orderTitle")),
        "currency": _safe_str(_get(order_msg, "totalCurrencyCode")),
        "totalAmount1000": _safe_int(_get(order_msg, "totalAmount1000")),
        "sellerJid": _safe_str(_get(order_msg, "sellerJID")),
        "catalogType": _safe_str(_get(order_msg, "catalogType")),
        "version": _safe_int(_get(order_msg, "messageVersion")),
        # Token is sensitive — never emit its value, only presence.
        "hasToken": _is_set(order_msg, "token"),
        "raw": protobuf_to_safe_dict(order_msg),
    }


def normalize_product(product_msg: Any) -> dict:
    """Normalize a ``ProductMessage`` (catalog snapshot + product snapshot)."""
    product = _get(product_msg, "product")
    catalog = _get(product_msg, "catalog")
    return {
        "businessOwnerJid": _safe_str(_get(product_msg, "businessOwnerJID")),
        "body": _safe_str(_get(product_msg, "body")),
        "footer": _safe_str(_get(product_msg, "footer")),
        "product": {
            "productId": _safe_str(_get(product, "productID")),
            "title": _safe_str(_get(product, "title")),
            "description": _safe_str(_get(product, "description")),
            "currency": _safe_str(_get(product, "currencyCode")),
            "priceAmount1000": _safe_int(_get(product, "priceAmount1000")),
            "salePriceAmount1000": _safe_int(_get(product, "salePriceAmount1000")),
            "retailerId": _safe_str(_get(product, "retailerID")),
            "url": _safe_str(_get(product, "URL")),
            "firstImageId": _safe_str(_get(product, "firstImageID")),
            "imageCount": _safe_int(_get(product, "productImageCount")),
        },
        "catalog": {
            "title": _safe_str(_get(catalog, "title")),
            "description": _safe_str(_get(catalog, "description")),
        },
        "raw": protobuf_to_safe_dict(product_msg),
    }


# ── Media metadata (generic, no download) ────────────────────────────────────

_MEDIA_FIELDS = (
    "imageMessage",
    "videoMessage",
    "ptvMessage",
    "audioMessage",
    "documentMessage",
    "documentWithCaptionMessage",
    "stickerMessage",
)


def normalize_media(raw: Any) -> dict:
    """Return safe media metadata for whichever media field is present."""
    for field in _MEDIA_FIELDS:
        if not _is_set(raw, field):
            continue
        media = _get(raw, field)
        info = {
            "mediaType": field,
            "mimetype": _safe_str(_get(media, "mimetype")),
            "fileLength": _safe_int(_get(media, "fileLength")),
            "caption": _safe_str(_get(media, "caption")),
            "fileName": _safe_str(_get(media, "fileName")),
            "isViewOnce": bool(_get(media, "viewOnce", False)),
            "isPTT": bool(_get(media, "PTT", False)),
            "isGif": bool(_get(media, "gifPlayback", False)),
            "isAnimated": bool(_get(media, "isAnimated", False)),
            "durationSeconds": _safe_int(_get(media, "seconds")),
        }
        return {k: v for k, v in info.items() if v not in ("", 0, False, None) or k == "mediaType"}
    return {}


# ── Safe protobuf serialization ──────────────────────────────────────────────

def protobuf_to_safe_dict(msg: Any, _depth: int = 0) -> Any:
    """Convert a protobuf (or arbitrary) object into a JSON-safe dict.

    - uses ``MessageToDict`` when available (present fields only);
    - falls back to a manual field walk for exotic/mock objects;
    - redacts sensitive keys and caps depth/size;
    - never raises.
    """
    if msg is None or _depth > _MAX_DEPTH:
        return None

    data: Any
    try:
        from google.protobuf.json_format import MessageToDict
        from google.protobuf.message import Message as _ProtoMessage

        if isinstance(msg, _ProtoMessage):
            data = _message_to_dict_compat(MessageToDict, msg)
        else:
            data = _manual_to_dict(msg, _depth)
    except Exception:
        data = _manual_to_dict(msg, _depth)

    return _sanitize(data, _depth)


def _message_to_dict_compat(message_to_dict, msg) -> dict:
    """Call ``MessageToDict`` across protobuf versions (present fields only)."""
    try:
        # protobuf >= 5.x
        return message_to_dict(
            msg,
            always_print_fields_with_no_presence=False,
            preserving_proto_field_name=True,
        )
    except TypeError:
        # older protobuf used including_default_value_fields
        return message_to_dict(
            msg,
            including_default_value_fields=False,
            preserving_proto_field_name=True,
        )


def _manual_to_dict(obj: Any, depth: int) -> Any:
    if isinstance(obj, (bytes, bytearray)):
        return _BYTES_PLACEHOLDER.format(n=len(obj))
    if isinstance(obj, dict):
        return {str(k): _manual_to_dict(v, depth + 1) for k, v in list(obj.items())[:_MAX_ITEMS]}
    if isinstance(obj, (list, tuple)):
        return [_manual_to_dict(v, depth + 1) for v in list(obj)[:_MAX_ITEMS]]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    # Generic object → best-effort __dict__ or repr.
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict) and d:
        return {str(k): _manual_to_dict(v, depth + 1) for k, v in list(d.items())[:_MAX_ITEMS]}
    return repr(obj)


def _sanitize(value: Any, depth: int) -> Any:
    """Redact sensitive keys and cap depth/size of an already-built structure."""
    if depth > _MAX_DEPTH:
        return "<max-depth>"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, val in list(value.items())[:_MAX_ITEMS]:
            if _is_sensitive_key(str(key)):
                out[str(key)] = REDACTED
            else:
                out[str(key)] = _sanitize(val, depth + 1)
        return out
    if isinstance(value, list):
        return [_sanitize(v, depth + 1) for v in value[:_MAX_ITEMS]]
    return value


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(sub in lowered for sub in _SENSITIVE_SUBSTRINGS)


# ── Envelope ─────────────────────────────────────────────────────────────────

def normalize_message_event(msg: Any, phone: str, session_id: str = "1") -> dict:
    """Build the canonical ``MessageEvent`` envelope from a Neonize ``MessageEv``."""
    info = _get(msg, "Info")
    raw = _get(msg, "Message")

    key = normalize_message_key(info, phone)
    context = normalize_context(raw)
    mtype = detect_type(raw)
    data = _normalize_data(mtype, raw)

    event = _EVENT_BY_TYPE.get(mtype, "message.unknown")
    if mtype == "interactiveResponseMessage":
        event = _native_flow_event(data)

    return {
        "event": event,
        "sessionId": session_id,
        "messageId": key["id"],
        "chatJid": key["chatJid"],
        "senderJid": key["senderJid"],
        "fromMe": key["fromMe"],
        "pushname": key["pushname"],
        "timestamp": key["timestamp"],
        "type": mtype,
        "data": data,
        "context": context,
        "raw": protobuf_to_safe_dict(raw),
    }


def _native_flow_event(data: dict) -> str:
    return "message.form_response" if data.get("kind") == "form" else "message.native_flow_response"


def _normalize_data(mtype: str, raw: Any) -> dict:
    """Produce the canonical ``data`` block for the detected type."""
    if mtype in ("conversation", "extendedTextMessage"):
        return {"text": _extract_text(raw)}
    if mtype in _MEDIA_FIELDS:
        return normalize_media(raw)
    if mtype == "contactMessage":
        ct = _get(raw, "contactMessage")
        return {"displayName": _safe_str(_get(ct, "displayName")), "vcard": _safe_str(_get(ct, "vcard"))}
    if mtype == "contactsArrayMessage":
        arr = _get(raw, "contactsArrayMessage")
        contacts = [
            {"displayName": _safe_str(_get(c, "displayName")), "vcard": _safe_str(_get(c, "vcard"))}
            for c in (_get(arr, "contacts", []) or [])
        ][:_MAX_ITEMS]
        return {"count": len(contacts), "contacts": contacts}
    if mtype in ("locationMessage", "liveLocationMessage"):
        loc = _get(raw, mtype)
        return {
            "lat": _get(loc, "degreesLatitude"),
            "lng": _get(loc, "degreesLongitude"),
            "name": _safe_str(_get(loc, "name")),
            "address": _safe_str(_get(loc, "address")),
        }
    if mtype == "reactionMessage":
        react = _get(raw, "reactionMessage")
        emoji = _safe_str(_get(react, "text"))
        return {
            "emoji": emoji,
            "targetMessageId": _safe_str(_get(_get(react, "key"), "ID")),
            "isRemoved": emoji == "",
        }
    if mtype in ("pollCreationMessage", "pollCreationV2Message", "pollCreationV3Message"):
        poll = _get(raw, mtype)
        options = [_safe_str(_get(o, "optionName")) for o in (_get(poll, "options", []) or [])]
        return {"pollName": _safe_str(_get(poll, "name")), "options": options}
    if mtype in ("pollUpdateMessage", "pollUpdateMessageMetadata"):
        vote = _get(raw, mtype)
        selected = [_safe_str(o) for o in (_get(_get(vote, "vote"), "selectedOptions", []) or [])]
        poll_id = _safe_str(_get(_get(vote, "pollCreationMessageKey"), "ID"))
        return {"pollId": poll_id or None, "selectedOptions": selected}
    if mtype == "interactiveResponseMessage":
        return normalize_native_flow_response(_get(raw, "interactiveResponseMessage"))
    if mtype == "orderMessage":
        return normalize_order(_get(raw, "orderMessage"))
    if mtype == "productMessage":
        return normalize_product(_get(raw, "productMessage"))
    # Unknown — expose field names for forward-compatible diagnostics.
    return {"rawType": mtype, "fields": _present_field_names(raw)}


def _extract_text(raw: Any) -> str:
    if _is_set(raw, "conversation"):
        return _safe_str(_get(raw, "conversation"))
    ext = _get(raw, "extendedTextMessage")
    return _safe_str(_get(ext, "text"))


def _present_field_names(raw: Any) -> list[str]:
    try:
        return [f[0].name for f in raw.ListFields()]
    except Exception:
        return []


def _enum_name(msg: Any, field: str) -> str | None:
    """Return the enum value name for a protobuf enum field, or ``None``."""
    try:
        descriptor = msg.DESCRIPTOR.fields_by_name[field]
        number = getattr(msg, field)
        if descriptor.enum_type and number:
            return descriptor.enum_type.values_by_number[number].name
    except Exception:
        pass
    return None


def _safe_str(value: Any) -> str:
    try:
        return "" if value is None else str(value)
    except Exception:
        return ""


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0