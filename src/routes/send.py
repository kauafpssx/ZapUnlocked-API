from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.send.sendMessage import send_message
from src.controllers.whatsapp.send.sendButton import send_with_buttons
from src.controllers.whatsapp.send.sendImage import send_image
from src.controllers.whatsapp.send.sendAudio import send_audio
from src.controllers.whatsapp.send.sendVideo import send_video
from src.controllers.whatsapp.send.sendDocument import send_document
from src.controllers.whatsapp.send.sendSticker import send_sticker
from src.controllers.whatsapp.send.sendReaction import send_reaction
from src.controllers.whatsapp.send.sendPoll import send_poll, send_poll_vote
from src.controllers.whatsapp.send.sendExtras import (
    send_location,
    send_contact,
    send_contacts,
    delete_msg,
    read_messages,
    send_link,
    send_edit,
)

router = APIRouter(dependencies=[Depends(auth)])

# ── Basic messages ────────────────────────────────────
router.post("/send")(send_message)
router.post("/send_wbuttons")(send_with_buttons)
router.post("/send_image")(send_image)
router.post("/send_audio")(send_audio)
router.post("/send_video")(send_video)
router.post("/send_document")(send_document)
router.post("/send_sticker")(send_sticker)
router.post("/send_reaction")(send_reaction)

# ── New routes ─────────────────────────────────────────
router.post("/send_location")(send_location)
router.post("/send_contact")(send_contact)
router.post("/send_contacts")(send_contacts)
router.post("/send_link")(send_link)

# ── Message management ─────────────────────────────────
router.post("/messages/delete")(delete_msg)
router.post("/messages/read")(read_messages)
router.post("/messages/edit")(send_edit)

# ── Interactive buttons ────────────────────────────────
router.post("/messages/send-button-list")(send_with_buttons)
router.post("/messages/send-button-actions")(send_with_buttons)
router.post("/messages/send-button-otp")(send_with_buttons)
router.post("/messages/send-button-pix")(send_with_buttons)
router.post("/messages/send-option-list")(send_with_buttons)

# ── Polls ──────────────────────────────────────────────
router.post("/messages/send-poll")(send_poll)
router.post("/messages/send-poll-vote")(send_poll_vote)
