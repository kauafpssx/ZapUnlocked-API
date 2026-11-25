from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.groups.groupsController import (
    list_groups,
    get_group,
    create_group,
    leave_group,
    invite_link,
    update_participants,
    update_settings,
    list_join_requests,
    update_join_requests,
)

router = APIRouter(dependencies=[Depends(auth)])

router.get("/groups")(list_groups)
router.post("/groups")(create_group)
router.get("/groups/{jid:path}")(get_group)
router.post("/groups/{jid:path}/leave")(leave_group)
router.get("/groups/{jid:path}/invite-link")(invite_link)
router.post("/groups/{jid:path}/participants")(update_participants)
router.get("/groups/{jid:path}/join-requests")(list_join_requests)
router.post("/groups/{jid:path}/join-requests")(update_join_requests)
router.patch("/groups/{jid:path}")(update_settings)