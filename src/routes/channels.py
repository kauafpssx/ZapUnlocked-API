from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.channels.channelsController import (
    get_info,
    get_info_by_invite,
    get_messages,
    follow,
    unfollow,
    react,
    mute,
)

router = APIRouter(dependencies=[Depends(auth)])

router.get("/channels/invite/{invite}")(get_info_by_invite)
router.get("/channels/{jid:path}")(get_info)
router.get("/channels/{jid:path}/messages")(get_messages)
router.post("/channels/{jid:path}/follow")(follow)
router.post("/channels/{jid:path}/unfollow")(unfollow)
router.post("/channels/{jid:path}/react")(react)
router.post("/channels/{jid:path}/mute")(mute)