import sqlite3
from pathlib import Path
from src.config.constants import AUTH_DIR
from neonize.utils import build_jid


def _get_db():
    db_path = Path(AUTH_DIR) / "auth.sqlite"
    if not db_path.exists():
        return None
    return str(db_path)


def resolve_jid(phone: str):
    db = _get_db()
    if not db:
        return build_jid(f"{phone}@s.whatsapp.net")
    try:
        conn = sqlite3.connect(db)
        cur = conn.execute(
            "SELECT lid FROM whatsmeow_lid_map WHERE pn = ?",
            (phone,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return build_jid(f"{row[0]}@lid")
    except Exception:
        pass
    return build_jid(f"{phone}@s.whatsapp.net")


def query_contact_db(phone: str):
    db = _get_db()
    if not db:
        return {}
    try:
        conn = sqlite3.connect(db)
        cur = conn.execute(
            "SELECT first_name, full_name, push_name, business_name FROM whatsmeow_contacts WHERE their_jid = ?",
            (f"{phone}@s.whatsapp.net",)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "firstName": row[0] or None,
                "fullName": row[1] or None,
                "pushName": row[2] or None,
                "businessName": row[3] or None,
            }
    except Exception:
        pass
    return {}
