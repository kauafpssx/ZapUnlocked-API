"""Message handling — callback detection, type routing, and helpers."""

from src.handlers.callback import handleMessage
from src.handlers.message_router import dispatch_message_event
from src.handlers.helpers import _has, _safe_str, _safe_int, _detect_type
