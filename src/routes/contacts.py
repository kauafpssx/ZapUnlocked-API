from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.contacts.contactController import get_contact_info
from src.controllers.whatsapp.contacts.contactExtrasController import (
    is_on_whatsapp,
    business_profile,
    user_devices,
    blocklist,
    privacy_settings,
)

router = APIRouter(dependencies=[Depends(auth)])

router.post("/info")(get_contact_info)
router.post("/is-on-whatsapp")(is_on_whatsapp)
router.get("/business-profile")(business_profile)
router.get("/devices")(user_devices)
router.get("/blocklist")(blocklist)
router.get("/privacy")(privacy_settings)
