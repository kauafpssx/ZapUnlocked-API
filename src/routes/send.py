from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.send.sendMessage import send_message
from src.controllers.whatsapp.send.sendButton import (
    send_with_buttons,
    send_otp,
    send_pix,
    send_quick_reply,
    send_url,
    send_call,
)
from src.controllers.whatsapp.send.sendImage import send_image
from src.controllers.whatsapp.send.sendAudio import send_audio
from src.controllers.whatsapp.send.sendVideo import send_video, send_gif
from src.controllers.whatsapp.send.sendDocument import send_document
from src.controllers.whatsapp.send.sendSticker import send_sticker
from src.controllers.whatsapp.send.sendReaction import send_reaction
from src.controllers.whatsapp.send.sendPoll import send_poll, send_poll_vote
from src.controllers.whatsapp.send.sendLocation import send_location
from src.controllers.whatsapp.send.sendContact import send_contact
from src.controllers.whatsapp.send.sendContacts import send_contacts
from src.controllers.whatsapp.send.sendLink import send_link
from src.controllers.whatsapp.send.sendDelete import delete_msg
from src.controllers.whatsapp.send.sendRead import read_messages
from src.controllers.whatsapp.send.sendEdit import send_edit
from src.controllers.whatsapp.send.sendOptionList import send_option_list
from src.controllers.whatsapp.send.sendBulk import send_bulk
from src.controllers.whatsapp.send.sendAlbum import send_album
from src.controllers.whatsapp.send.sendStickerPack import send_sticker_pack
from src.controllers.status.messageStatusController import get_message_status
from src.controllers.whatsapp.send.sendPinPresence import pin_message, send_presence
from src.controllers.whatsapp.send.sendNativeFlow import send_native_flow
from src.controllers.whatsapp.send.sendInteractive import send_interactive, send_carousel

router = APIRouter(dependencies=[Depends(auth)])

# ── Media (url OR file upload) ────────────────────────
router.post("/send_image")(send_image)
router.post("/send_audio")(send_audio)
router.post("/send_video")(send_video)
router.post("/send_document")(send_document)
router.post("/send_gif")(send_gif)
router.post("/send_sticker")(send_sticker)
router.post("/send_sticker_sound")(send_sticker)
router.get("/messages/{message_id}/status")(get_message_status)

# ── Basic messages ────────────────────────────────────
router.post("/send")(send_message)
router.post("/send_bulk")(send_bulk)
router.post("/messages/send-album")(send_album)
router.post("/messages/send-sticker-pack")(send_sticker_pack)
router.post("/messages/pin")(pin_message)
router.post("/messages/presence")(send_presence)
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
router.post("/messages/send-button-otp")(send_otp)
router.post("/messages/send-button-pix")(send_pix)
router.post("/messages/send-button-quick-reply")(send_quick_reply)
router.post("/messages/send-button-url")(send_url)
router.post("/messages/send-button-call")(send_call)
router.post("/messages/send-option-list")(send_option_list)
router.post("/messages/send-native-flow")(send_native_flow)
router.post("/messages/send-interactive")(send_interactive)
router.post("/messages/send-carousel")(send_carousel)

# ── Polls ──────────────────────────────────────────────
router.post("/messages/send-poll")(send_poll)
router.post("/messages/send-poll-vote")(send_poll_vote)
