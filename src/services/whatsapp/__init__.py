"""
WhatsApp services package.

Re-exports are lazy (PEP 562) so that simply importing the package
or its submodules (state, state_manager) does NOT eagerly load
neonize (which requires the libmagic C library).
"""

import importlib

_LAZY_IMPORTS = {
    # Connection lifecycle — imported from state.py (no neonize deps)
    "get_is_ready": ".state",
    "get_client": ".state",
    "get_qr": ".state",
    "get_reaction_cache": ".state",
    "get_qr_expires_in": ".state",
    # Connection lifecycle — imported from client.py (requires neonize)
    "start_bot": ".client",
    "logout": ".client",
    "activate_qr": ".client",
    # DB cleanup (db_cleanup.py)
    "cleanup_db": ".db_cleanup",
    "set_cleanup_interval": ".db_cleanup",
    "get_cleanup_state": ".db_cleanup",
    # Senders (sender/ subpackage)
    "send_message": ".sender",
    "send_button_message": ".sender",
    "send_image_message": ".sender",
    "send_audio_message": ".sender",
    "send_video_message": ".sender",
    "send_document_message": ".sender",
    "send_sticker_message": ".sender",
    "send_reaction": ".sender",
    "find_message": ".sender",
    # Message fetching (messageFetcher.py)
    "fetch_messages": ".messageFetcher",
    "get_recent_chats": ".messageFetcher",
}


def __getattr__(name):
    """Lazily import and cache the requested symbol."""
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name], __package__)
        attr = getattr(module, name)
        globals()[name] = attr  # cache for subsequent access
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
