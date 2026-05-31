"""Shared helpers for message handling."""


def _has(obj, field: str) -> bool:
    """Check if a protobuf object has a non-default field."""
    try:
        val = getattr(obj, field)
        return val is not None and val != type(val)()
    except Exception:
        return False


def _safe_str(obj, field: str) -> str:
    """Safely extract a string field from a protobuf object."""
    try:
        return str(getattr(obj, field) or "")
    except Exception:
        return ""


def _safe_int(obj, field: str) -> int:
    """Safely extract an int field from a protobuf object."""
    try:
        return int(getattr(obj, field) or 0)
    except Exception:
        return 0


def _detect_type(raw) -> str:
    """Detect which message type field is set on a protobuf Message."""
    for field in [
        "conversation", "extendedTextMessage", "imageMessage", "videoMessage",
        "audioMessage", "documentMessage", "stickerMessage", "contactMessage",
        "locationMessage", "reactionMessage", "pollCreationMessage", "pollUpdateMessage",
        "interactiveResponseMessage", "interactiveMessage", "buttonsResponseMessage",
        "templateButtonReplyMessage", "listResponseMessage", "protocolMessage", "senderKeyDistributionMessage",
    ]:
        try:
            val = getattr(raw, field)
            if val is not None and val != type(val)():
                return field
        except Exception:
            pass
    return "unknown"
