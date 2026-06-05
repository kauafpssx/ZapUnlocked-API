from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.settings.privacyController import (
    set_last_seen,
    set_online,
    set_profile,
    set_status,
    set_read_receipts,
    set_groups_add,
    set_call_add,
    set_about,
    set_disappearing_timer,
)
from src.controllers.whatsapp.settings.profileController import update_my_profile
from src.controllers.whatsapp.contacts.blockController import block_user
from src.controllers.whatsapp.settings.ipControlController import get_ip_control, update_ip_control
from src.controllers.whatsapp.settings.instanceController import (
    set_call_reject_auto,
    set_call_reject_message,
    set_auto_read_message,
    get_phone_pair_code,
)
from src.controllers.system.ipRulesController import (
    get_ip_rules,
    add_to_whitelist,
    add_to_blacklist,
    remove_from_whitelist,
    remove_from_blacklist,
)

router = APIRouter(dependencies=[Depends(auth)])

# Profile & block
router.post("/profile")(update_my_profile)
router.post("/block")(block_user)

# Privacy — per-param routes
router.put("/privacy/last-seen")(set_last_seen)
router.put("/privacy/online")(set_online)
router.put("/privacy/profile")(set_profile)
router.put("/privacy/status")(set_status)
router.put("/privacy/read-receipts")(set_read_receipts)
router.put("/privacy/groups-add")(set_groups_add)
router.put("/privacy/call-add")(set_call_add)
router.put("/privacy/about")(set_about)
router.put("/privacy/disappearing-timer")(set_disappearing_timer)

# IP Control toggle
router.get("/ip-control")(get_ip_control)
router.put("/ip-control")(update_ip_control)

# Instance Settings
router.put("/instance/call-reject-auto")(set_call_reject_auto)
router.put("/instance/call-reject-message")(set_call_reject_message)
router.put("/instance/auto-read-message")(set_auto_read_message)
router.get("/phone-code/{phone}")(get_phone_pair_code)

# IP Rules (blacklist / whitelist)
router.get("/ip-rules")(get_ip_rules)
router.post("/ip-rules/whitelist")(add_to_whitelist)
router.post("/ip-rules/blacklist")(add_to_blacklist)
router.delete("/ip-rules/whitelist/{ip}")(remove_from_whitelist)
router.delete("/ip-rules/blacklist/{ip}")(remove_from_blacklist)
