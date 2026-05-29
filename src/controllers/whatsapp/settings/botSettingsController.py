from typing import Optional, List
from pydantic import BaseModel
from fastapi import HTTPException
from src.services.whatsapp import settingsService

class BotSettingsIn(BaseModel):
    ai_tag_enabled: Optional[bool] = None
    ai_tag_text: Optional[str] = None
    ip_control_enabled: Optional[bool] = None
    ip_whitelist: Optional[List[str]] = None
    ip_blacklist: Optional[List[str]] = None

def get_bot_settings():
    return {"success": True, "settings": settingsService.get_settings()}

def update_bot_settings(data: BotSettingsIn):
    try:
        update_data = {}
        if data.ai_tag_enabled is not None:
            update_data["ai_tag_enabled"] = data.ai_tag_enabled
        if data.ai_tag_text is not None:
            update_data["ai_tag_text"] = data.ai_tag_text
        if data.ip_control_enabled is not None:
            update_data["ip_control_enabled"] = data.ip_control_enabled
        if data.ip_whitelist is not None:
            update_data["ip_whitelist"] = data.ip_whitelist
        if data.ip_blacklist is not None:
            update_data["ip_blacklist"] = data.ip_blacklist
            
        settings = settingsService.save_settings(update_data)
        return {"success": True, "message": "Bot settings updated.", "settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
