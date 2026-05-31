"""
IP Rules Controller — manage blacklist / whitelist via API.

Endpoints (registered in routes/settings.py):
  GET    /settings/ip-rules           → list current rules
  POST   /settings/ip-rules/whitelist  → add IP to whitelist
  POST   /settings/ip-rules/blacklist  → add IP to blacklist
  DELETE /settings/ip-rules/whitelist   → remove IP from whitelist
  DELETE /settings/ip-rules/blacklist   → remove IP from blacklist
"""

from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException
from src.services import ip_rules_service


# ── Schemas ────────────────────────────────────────────────────────
class IpRuleRequest(BaseModel):
    ip: str
    """The IP address (v4 or v6) to add / remove."""

    list_name: Optional[str] = None
    """Deprecated — use the endpoint path instead."""


# ── Helpers ────────────────────────────────────────────────────────
def _parse_ip_rules(rules: dict) -> dict:
    """Wrap rules in a standard success envelope."""
    return {
        "success": True,
        "rules": {
            "whitelist": rules.get("whitelist", []),
            "blacklist": rules.get("blacklist", []),
        },
    }


# ── Handlers ───────────────────────────────────────────────────────
async def get_ip_rules():
    """Return the current whitelist and blacklist."""
    return _parse_ip_rules(ip_rules_service.get_ip_rules())


async def add_to_whitelist(data: IpRuleRequest):
    """Add an IP address to the whitelist."""
    try:
        rules = ip_rules_service.add_ip("whitelist", data.ip)
        return {
            **_parse_ip_rules(rules),
            "message": f"IP {data.ip} added to whitelist.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def add_to_blacklist(data: IpRuleRequest):
    """Add an IP address to the blacklist."""
    try:
        rules = ip_rules_service.add_ip("blacklist", data.ip)
        return {
            **_parse_ip_rules(rules),
            "message": f"IP {data.ip} added to blacklist.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def remove_from_whitelist(ip: str):
    """Remove an IP address from the whitelist."""
    try:
        rules = ip_rules_service.remove_ip("whitelist", ip)
        return {
            **_parse_ip_rules(rules),
            "message": f"IP {ip} removed from whitelist.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


async def remove_from_blacklist(ip: str):
    """Remove an IP address from the blacklist."""
    try:
        rules = ip_rules_service.remove_ip("blacklist", ip)
        return {
            **_parse_ip_rules(rules),
            "message": f"IP {ip} removed from blacklist.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
