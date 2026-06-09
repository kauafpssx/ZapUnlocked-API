"""URL prefix → folder structure mapping.

Each entry: (path_prefix, [folder, subfolder, ...])
Longer prefixes win over shorter ones (longest-prefix-match).
None prefix = catch-all for "Other".

NOTE: Prefixes with `/` separators only — cannot use `-` or `_` as path separators.
For routes like /messages/send-button-list, add explicit entries.
"""

from typing import Dict, List, Optional, Tuple

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

    # ── Logs (separate folder) ────────────────────────────────────────
    ("/logs", ["Logs"]),

    # ── Messages (plain send) ─────────────────────────────────────────
    ("/send",            ["Messages", "Text"]),
    ("/send_bulk",       ["Messages", "Text"]),
    ("/send_image",      ["Messages", "Media"]),
    ("/send_audio",      ["Messages", "Media"]),
    ("/send_video",      ["Messages", "Media"]),
    ("/send_document",   ["Messages", "Media"]),
    ("/send_sticker",    ["Messages", "Media"]),
    ("/send_gif",        ["Messages", "Media"]),
    ("/send_location",   ["Messages", "Location"]),
    ("/send_contact",    ["Messages", "Contact"]),
    ("/send_contacts",   ["Messages", "Contact"]),
    ("/send_link",       ["Messages", "Link"]),
    ("/send_reaction",   ["Messages", "Reaction"]),

    # ── Interactive Messages > Buttons ────────────────────────────────
    ("/messages/send-option-list",       ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-list",       ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-url",        ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-call",       ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-otp",        ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-pix",        ["Interactive Messages", "Buttons"]),
    ("/messages/send-button-quick-reply",["Interactive Messages", "Buttons"]),

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
    ("/management/export",          ["Management", "Export/Import"]),
    ("/management/import",          ["Management", "Export/Import"]),
    ("/management/chats",           ["Management", "Chats"]),
    ("/management/contacts/{phone}",["Management", "Contacts"]),
    ("/management/groups",          ["Management", "Groups"]),

    # ── Settings ──────────────────────────────────────────────────────
    ("/settings/profile",    ["Settings", "Profile"]),
    ("/settings/privacy",    ["Settings", "Privacy"]),
    ("/settings/ip-control", ["Settings", "IP Control"]),
    ("/settings/ip-rules",   ["Settings", "IP Rules"]),

    # ── Status ────────────────────────────────────────────────────────
    ("/status",         ["Status", "General"]),
    ("/stats",          ["Status", "General"]),
    ("/status/health",   ["Status", "Health"]),
    ("/status/readiness",["Status", "Health"]),
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


def find_folder(path: str) -> List[str]:
    """Find the best folder path for a given URL path."""
    matches = []
    for prefix, folders in FOLDER_MAP:
        if prefix is None:
            continue
        if path == prefix or path.startswith(prefix + "/"):
            matches.append((len(prefix), folders))

    if not matches:
        # Auto-fallback: /foo/bar/baz → ["Foo", "Bar"]
        parts = [p for p in path.split("/") if p and not p.startswith("{")]
        if parts:
            return [p.replace("-", " ").replace("_", " ").title().strip() for p in parts[:2]]
        return ["Other"]

    matches.sort(key=lambda x: -x[0])
    return matches[0][1]
