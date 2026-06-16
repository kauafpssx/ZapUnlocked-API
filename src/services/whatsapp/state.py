"""Backward-compatible shim — functional API lives in state_manager."""
from src.services.whatsapp.state_manager import (  # noqa: F401
    get_client, set_client,
    get_is_ready, set_is_ready,
    get_qr, set_current_qr,
    get_reaction_cache,
    get_main_loop, set_main_loop,
    get_qr_generation_active, set_qr_generation_active,
    get_qr_last_generated_at, set_qr_last_generated_at,
    get_qr_url_logged, set_qr_url_logged,
    get_keep_qr_active_on_restart, set_keep_qr_active_on_restart,
    get_qr_expires_in,
    set_current_pair_code,
    get_start_time, get_connected_at, set_connected_at,
    get_cleanup_lock,
    mark_connected, mark_disconnected,
    reset_for_reconnect, reset_for_logout,
)
