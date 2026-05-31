"""
IP Rules Service — manages blacklist/whitelist in a dedicated JSON file.

The file (data/ip_rules.json) is kept separate from general bot settings
so it can be edited directly or managed via API endpoints.
"""

import json
from pathlib import Path
from typing import Optional
from src.config.constants import DATA_DIR
from src.utils.logger import logger

RULES_FILE = Path(DATA_DIR) / "ip_rules.json"

DEFAULT_RULES: dict = {
    "whitelist": [],
    "blacklist": [],
}


def _ensure_file():
    """Create the rules file with defaults if it doesn't exist."""
    if not RULES_FILE.exists():
        RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        _write_rules(DEFAULT_RULES)


def _read_rules() -> dict:
    """Read the current rules from disk."""
    _ensure_file()
    try:
        content = RULES_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return DEFAULT_RULES.copy()
        rules = json.loads(content)
        # Ensure both keys exist
        for key in DEFAULT_RULES:
            if key not in rules:
                rules[key] = []
        return rules
    except Exception as e:
        logger.error(f"Failed to read IP rules: {e}")
        return DEFAULT_RULES.copy()


def _write_rules(rules: dict):
    """Write rules to disk atomically."""
    try:
        RULES_FILE.write_text(
            json.dumps(rules, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error(f"Failed to write IP rules: {e}")


def get_ip_rules() -> dict:
    """Return the full rules dict (whitelist + blacklist)."""
    return _read_rules()


def add_ip(list_name: str, ip: str) -> dict:
    """
    Add an IP to a list ('whitelist' or 'blacklist').

    Returns the updated rules dict.
    Raises ValueError if list_name is invalid.
    """
    if list_name not in ("whitelist", "blacklist"):
        raise ValueError(f"Invalid list name: '{list_name}'. Use 'whitelist' or 'blacklist'.")

    rules = _read_rules()
    if ip not in rules[list_name]:
        rules[list_name].append(ip)
        _write_rules(rules)
        logger.info(f"IP {ip} added to {list_name}")
    else:
        logger.info(f"IP {ip} already in {list_name}")
    return rules


def remove_ip(list_name: str, ip: str) -> dict:
    """
    Remove an IP from a list ('whitelist' or 'blacklist').

    Returns the updated rules dict.
    Raises ValueError if list_name is invalid.
    """
    if list_name not in ("whitelist", "blacklist"):
        raise ValueError(f"Invalid list name: '{list_name}'. Use 'whitelist' or 'blacklist'.")

    rules = _read_rules()
    if ip in rules[list_name]:
        rules[list_name].remove(ip)
        _write_rules(rules)
        logger.info(f"IP {ip} removed from {list_name}")
    else:
        logger.info(f"IP {ip} not found in {list_name}")
    return rules


def is_ip_blocked(ip: str) -> bool:
    """Check if an IP is in the blacklist."""
    rules = _read_rules()
    return ip in rules["blacklist"]


def is_ip_allowed(ip: str) -> Optional[bool]:
    """
    Check if an IP is allowed.

    Returns:
      - True  if whitelist is empty OR IP is in whitelist
      - False if whitelist is non-empty AND IP is NOT in whitelist
      - None  if IP is blacklisted (explicitly denied)
    """
    rules = _read_rules()

    # Blacklist takes priority
    if ip in rules["blacklist"]:
        return None

    # Whitelist: if empty, everyone is allowed
    if not rules["whitelist"]:
        return True

    # Non-empty whitelist: IP must be present
    return ip in rules["whitelist"]
