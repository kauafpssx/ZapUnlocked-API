"""JID / phone number utilities."""


def resolve_jid(phone: str) -> str:
    """Return a full WhatsApp JID string from a phone number or existing JID.

    - "5511999999999"           → "5511999999999@s.whatsapp.net"
    - "120363XXXXXXXX@g.us"    → "120363XXXXXXXX@g.us"  (group)
    - "5511999999999@s.whatsapp.net" → unchanged
    """
    clean = phone.replace(" ", "").replace("+", "")
    if "@" in clean:
        return clean
    return f"{clean}@s.whatsapp.net"
