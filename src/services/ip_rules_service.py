"""IP Rules Service — manages blacklist/whitelist in SQLite."""

from typing import Optional

from src.utils.db import get_conn
from src.utils.logger import logger


def get_ip_rules() -> dict:
    conn = get_conn()
    rows = conn.execute("SELECT list_name, ip FROM ip_rules").fetchall()
    result: dict = {"whitelist": [], "blacklist": []}
    for row in rows:
        result[row["list_name"]].append(row["ip"])
    return result


def add_ip(list_name: str, ip: str) -> dict:
    if list_name not in ("whitelist", "blacklist"):
        raise ValueError(f"Invalid list name: '{list_name}'. Use 'whitelist' or 'blacklist'.")
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO ip_rules (list_name, ip) VALUES (?, ?)",
        (list_name, ip),
    )
    conn.commit()
    logger.info(f"IP {ip} added to {list_name}")
    return get_ip_rules()


def remove_ip(list_name: str, ip: str) -> dict:
    if list_name not in ("whitelist", "blacklist"):
        raise ValueError(f"Invalid list name: '{list_name}'. Use 'whitelist' or 'blacklist'.")
    conn = get_conn()
    conn.execute(
        "DELETE FROM ip_rules WHERE list_name=? AND ip=?",
        (list_name, ip),
    )
    conn.commit()
    return get_ip_rules()


def is_ip_blocked(ip: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM ip_rules WHERE list_name='blacklist' AND ip=?", (ip,)
    ).fetchone()
    return row is not None


def is_ip_allowed(ip: str) -> Optional[bool]:
    conn = get_conn()
    if conn.execute(
        "SELECT 1 FROM ip_rules WHERE list_name='blacklist' AND ip=?", (ip,)
    ).fetchone():
        return None
    count = conn.execute(
        "SELECT COUNT(*) FROM ip_rules WHERE list_name='whitelist'"
    ).fetchone()[0]
    if count == 0:
        return True
    return conn.execute(
        "SELECT 1 FROM ip_rules WHERE list_name='whitelist' AND ip=?", (ip,)
    ).fetchone() is not None
