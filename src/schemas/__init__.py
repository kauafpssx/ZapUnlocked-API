"""Domain-separated Pydantic request schemas.

All public symbols are re-exported here so existing imports like
    from src.schemas import SendMessageRequest
continue to work without changes.
"""

from src.schemas.send import (
    BaseWhatsAppRequest,
    SendMessageRequest,
    SendMediaRequest,
    SendVideoRequest,
    SendAudioRequest,
    SendReactionRequest,
    SendStickerRequest,
    SendDocumentRequest,
    SendButtonRequest,
    SendButtonOtpRequest,
    SendButtonPixRequest,
    SendButtonQuickReplyRequest,
    SendButtonUrlRequest,
    SendButtonCallRequest,
    SendOptionListRequest,
    SendPollRequest,
    SendPollVoteRequest,
    SendLocationRequest,
    ContactItem,
    SendContactRequest,
    SendContactsRequest,
    SendLinkRequest,
    DeleteMessageRequest,
    ReadMessagesRequest,
    SendEditMessageRequest,
    BulkSendTextRequest,
)
from src.schemas.settings import (
    ProfileUpdateRequest,
    PrivacyUpdateRequest,
    UpdateInstanceNameRequest,
    CallRejectRequest,
    CallRejectMessageRequest,
    AutoReadRequest,
)
from src.schemas.contacts import BlockRequest
from src.schemas.webhooks import (
    WebhookCreateRequest,
    WebhookUpdateRequest,
    WebhookToggleRequest,
)
