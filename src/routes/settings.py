from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.settings.privacyController import update_privacy
from src.controllers.whatsapp.settings.profileController import update_my_profile
from src.controllers.whatsapp.contacts.blockController import block_user
from src.controllers.whatsapp.settings.botSettingsController import get_bot_settings, update_bot_settings
from src.controllers.whatsapp.settings.instanceController import (
    set_call_reject_auto,
    set_call_reject_message,
    set_auto_read_message,
    get_phone_pair_code,
)

router = APIRouter(dependencies=[Depends(auth)])

# Profile & Privacy
router.post("/privacy")(update_privacy)
router.post("/profile")(update_my_profile)
router.post("/block")(block_user)

# Bot Settings (AI Tag, etc)
router.get("/bot")(get_bot_settings)
router.post("/bot")(update_bot_settings)

# Instance Settings
router.put("/instance/call-reject-auto")(set_call_reject_auto)
router.put("/instance/call-reject-message")(set_call_reject_message)
router.put("/instance/auto-read-message")(set_auto_read_message)
router.get("/phone-code/{phone}")(get_phone_pair_code)
