from pydantic import BaseModel
from fastapi import HTTPException
from src.services.whatsapp import settingsService


class IpControlRequest(BaseModel):
    enabled: bool


def get_ip_control():
    s = settingsService.get_settings()
    return {"success": True, "ip_control_enabled": s.get("ip_control_enabled", False)}


def update_ip_control(data: IpControlRequest):
    try:
        s = settingsService.save_settings({"ip_control_enabled": data.enabled})
        return {"success": True, "ip_control_enabled": s.get("ip_control_enabled")}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
