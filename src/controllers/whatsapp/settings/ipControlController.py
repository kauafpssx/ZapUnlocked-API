from src.utils.decorators import get_session_id
from pydantic import BaseModel
from fastapi import HTTPException, Request
from src.services.whatsapp import settingsService


class IpControlRequest(BaseModel):
    enabled: bool


def get_ip_control(request: Request = None):
    sid = get_session_id(request)
    s = settingsService.get_settings(sid)
    return {"success": True, "ip_control_enabled": s.get("ip_control_enabled", False)}


def update_ip_control(data: IpControlRequest, request: Request = None):
    sid = get_session_id(request)
    try:
        s = settingsService.save_settings({"ip_control_enabled": data.enabled}, sid)
        return {"success": True, "ip_control_enabled": s.get("ip_control_enabled")}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
