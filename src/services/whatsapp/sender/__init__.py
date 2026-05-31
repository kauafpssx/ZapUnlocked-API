"""
WhatsApp sender — split into feature modules for maintainability.

All public symbols are re-exported here so existing imports like
    from src.services.whatsapp.sender import send_message
continue to work without changes.

Modules:
  helpers.py    — build_jid, _ensure_client, _save_to_history, _build_context_info, _build_message_info
  text.py       — send_message
  media.py      — send_image_message, send_audio_message, send_video_message, send_document_message
  sticker.py    — send_sticker_message
  interactive.py — send_button_message, send_poll_message, send_poll_vote_message, find_message
  actions.py    — send_reaction, send_location_message, send_contact_message, send_contacts_message,
                  send_link_message, delete_message, mark_messages_read, edit_message
"""

from src.services.whatsapp.sender.text import send_message
from src.services.whatsapp.sender.media import (
    send_image_message,
    send_audio_message,
    send_video_message,
    send_document_message,
)
from src.services.whatsapp.sender.sticker import send_sticker_message
from src.services.whatsapp.sender.interactive import (
    send_button_message,
    send_poll_message,
    send_poll_vote_message,
    find_message,
)
from src.services.whatsapp.sender.actions import (
    send_reaction,
    send_location_message,
    send_contact_message,
    send_contacts_message,
    send_link_message,
    delete_message,
    mark_messages_read,
    edit_message,
)
