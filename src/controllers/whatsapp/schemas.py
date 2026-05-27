from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class BaseWhatsAppRequest(BaseModel):
    phone: str
    reply: Optional[str] = None
    type: Optional[str] = None
    quoted_id: Optional[str] = None

class SendMessageRequest(BaseWhatsAppRequest):
    message: str

class SendMediaRequest(BaseWhatsAppRequest):
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    document_url: Optional[str] = None
    sticker_url: Optional[str] = None
    caption: Optional[str] = ""
    fileName: Optional[str] = None
    mimetype: Optional[str] = None
    asDocument: Optional[bool] = False

class SendVideoRequest(BaseWhatsAppRequest):
    video_url: str
    caption: Optional[str] = ""
    gifPlayback: Optional[bool] = False
    ptv: Optional[bool] = False
    asDocument: Optional[bool] = False

class SendAudioRequest(BaseWhatsAppRequest):
    audio_url: str
    ptt: Optional[bool] = False
    asDocument: Optional[bool] = False
    format: Optional[str] = "m4a"

class SendReactionRequest(BaseWhatsAppRequest):
    reaction: Optional[str] = None
    messageId: Optional[str] = None
    text: Optional[str] = None
    emoji: Optional[str] = None

class SendStickerRequest(BaseWhatsAppRequest):
    sticker_url: Optional[str] = None
    image_url: Optional[str] = None
    pack: Optional[str] = None
    author: Optional[str] = None
    resizeMode: Optional[str] = "pad"
    padColor: Optional[str] = "black"
    blurIntensity: Optional[int] = 20

class SendDocumentRequest(BaseWhatsAppRequest):
    document_url: str
    fileName: Optional[str] = None

class SendButtonRequest(BaseWhatsAppRequest):
    message: Optional[str] = None
    text: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    footer: Optional[str] = None
    buttons: Optional[List[Dict[str, Any]]] = None
    button_text: Optional[str] = None
    button_id: Optional[str] = None
    button_value: Optional[str] = None
    webhook: Optional[Dict[str, Any]] = None
    reaction: Optional[str] = None
    # OTP/PIX button extensions
    code: Optional[str] = None
    pixKey: Optional[str] = None
    pixType: Optional[str] = None
    merchantName: Optional[str] = None
    image: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    newProfilePictureUrl: Optional[str] = None

class PrivacyUpdateRequest(BaseModel):
    lastSeen: Optional[str] = None          # all | contacts | none | match_last_seen
    online: Optional[str] = None            # all | contacts | none | match_last_seen
    profile: Optional[str] = None           # all | contacts | none
    status: Optional[str] = None            # all | contacts | none
    readReceipts: Optional[str] = None      # all | contacts | none
    groupsAdd: Optional[str] = None         # all | contacts | none
    callAdd: Optional[str] = None           # all | contacts | none
    about: Optional[str] = None             # status message (bio)
    disappearingTimer: Optional[int] = None # horas (0 = desligar, 24 = 1 dia, 168 = 7 dias)

class SendPollRequest(BaseWhatsAppRequest):
    name: str
    options: List[str]
    selectableCount: Optional[int] = 1

class SendPollVoteRequest(BaseWhatsAppRequest):
    pollId: Optional[str] = None
    pollName: Optional[str] = None
    options: List[str]

class UpdateInstanceNameRequest(BaseModel):
    name: str

# ── Settings / Instance ────────────────────────────────

class CallRejectRequest(BaseModel):
    value: bool

class CallRejectMessageRequest(BaseModel):
    value: str

class AutoReadRequest(BaseModel):
    value: bool

class PairPhoneRequest(BaseModel):
    phone: str

# ── Contacts ──────────────────────────────────────────

class BlockRequest(BaseModel):
    phone: str
    action: str  # "block" | "unblock"

# ── Novas features ─────────────────────────────────────

class SendLocationRequest(BaseWhatsAppRequest):
    lat: float
    lng: float
    name: Optional[str] = ""
    address: Optional[str] = ""

class ContactItem(BaseModel):
    name: str
    phone: str

class SendContactRequest(BaseWhatsAppRequest):
    name: str
    contactPhone: str

class SendContactsRequest(BaseWhatsAppRequest):
    contacts: List[ContactItem]

class SendLinkRequest(BaseWhatsAppRequest):
    url: str
    text: Optional[str] = ""
    title: Optional[str] = ""
    description: Optional[str] = ""
    thumbnailUrl: Optional[str] = None

class DeleteMessageRequest(BaseModel):
    phone: str
    messageId: str
    fromMe: Optional[bool] = True
    type: Optional[str] = "id"

class ReadMessagesRequest(BaseModel):
    phone: str
    messageIds: List[str]
    sender: Optional[str] = None
    type: Optional[str] = "id"

class SendEditMessageRequest(BaseWhatsAppRequest):
    messageId: str
    message: str
