"""Schema validation tests — exercise all Pydantic request models."""

import pytest
from pydantic import ValidationError

from src.schemas import (
    SendMessageRequest,
    SendMediaRequest,
    SendButtonRequest,
    SendPollRequest,
    SendLocationRequest,
    SendContactRequest,
    SendLinkRequest,
    DeleteMessageRequest,
    ReadMessagesRequest,
    SendEditMessageRequest,
    BlockRequest,
    WebhookCreateRequest,
    SendAudioRequest,
    SendVideoRequest,
    SendStickerRequest,
    SendDocumentRequest,
    SendReactionRequest,
)


# ═══════════════════════════════════════════════════════════════════════════
# SEND SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class TestSendMessageRequest:
    def test_valid(self):
        req = SendMessageRequest(phone="5511999999999", message="Hello")
        assert req.phone == "5511999999999"
        assert req.message == "Hello"

    def test_missing_phone_raises(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(message="Hello")

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(phone="5511999999999")


class TestSendMediaRequest:
    def test_minimal_valid(self):
        req = SendMediaRequest(phone="5511999999999")
        assert req.caption == ""
        assert req.asDocument is False
        assert req.fileName is None

    def test_with_all_fields(self):
        req = SendMediaRequest(
            phone="5511999999999",
            caption="Look at this!",
            asDocument=True,
            fileName="photo.jpg",
        )
        assert req.caption == "Look at this!"
        assert req.asDocument is True
        assert req.fileName == "photo.jpg"


class TestSendButtonRequest:
    def test_with_buttons(self):
        req = SendButtonRequest(
            phone="5511999999999",
            text="Choose one",
            buttons=[{"text": "A"}, {"text": "B"}],
        )
        assert len(req.buttons) == 2

    def test_buttons_optional(self):
        """buttons field is Optional, so omitting it is valid."""
        req = SendButtonRequest(phone="5511999999999", text="Choose")
        assert req.buttons is None


class TestSendPollRequest:
    def test_valid(self):
        req = SendPollRequest(
            phone="5511999999999",
            name="Favorite color",
            options=["Red", "Blue", "Green"],
        )
        assert req.selectableCount == 1
        assert len(req.options) == 3

    def test_min_options(self):
        req = SendPollRequest(
            phone="5511999999999",
            name="Yes or No?",
            options=["Yes", "No"],
        )
        assert len(req.options) == 2


class TestSendLocationRequest:
    def test_valid(self):
        req = SendLocationRequest(phone="5511999999999", lat=-23.5, lng=-46.6)
        assert req.name == ""
        assert req.address == ""

    def test_any_float_works(self):
        """lat/lng are plain float fields without constraints."""
        req = SendLocationRequest(phone="5511999999999", lat=999.0, lng=-999.0)
        assert req.lat == 999.0


class TestSendContactRequest:
    def test_valid(self):
        req = SendContactRequest(
            phone="5511999999999",
            name="John",
            contactPhone="5511988888888",
        )
        assert req.contactPhone == "5511988888888"


class TestSendLinkRequest:
    def test_requires_url(self):
        req = SendLinkRequest(phone="5511999999999", url="https://example.com")
        assert str(req.url) == "https://example.com/"

    def test_invalid_url_raises(self):
        with pytest.raises(ValidationError):
            SendLinkRequest(phone="5511999999999", url="not-a-url")


class TestDeleteMessageRequest:
    def test_defaults(self):
        req = DeleteMessageRequest(phone="5511999999999", messageId="abc123")
        assert req.fromMe is True
        assert req.type == "id"


class TestReadMessagesRequest:
    def test_valid(self):
        req = ReadMessagesRequest(phone="5511999999999", messageIds=["id1", "id2"])
        assert len(req.messageIds) == 2


class TestSendEditMessageRequest:
    def test_valid(self):
        req = SendEditMessageRequest(
            phone="5511999999999",
            messageId="abc",
            message="New text",
        )
        assert req.message == "New text"


class TestAudioRequest:
    def test_valid(self):
        req = SendAudioRequest(phone="5511999999999", audio_url="https://example.com/audio.mp3")
        assert req.ptt is False
        assert req.format == "m4a"


class TestVideoRequest:
    def test_valid(self):
        req = SendVideoRequest(phone="5511999999999", video_url="https://example.com/video.mp4")
        assert req.caption == ""
        assert req.gifPlayback is False


class TestStickerRequest:
    def test_valid(self):
        req = SendStickerRequest(phone="5511999999999")
        assert req.pack is None
        assert req.resizeMode == "pad"
        assert req.blurIntensity == 20


class TestDocumentRequest:
    def test_valid(self):
        req = SendDocumentRequest(
            phone="5511999999999",
            document_url="https://example.com/doc.pdf",
        )
        assert req.fileName is None


class TestReactionRequest:
    def test_valid(self):
        req = SendReactionRequest(
            phone="5511999999999",
            messageId="abc123",
            reaction="👍",
        )
        assert req.reaction == "👍"


# ═══════════════════════════════════════════════════════════════════════════
# CONTACT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class TestBlockRequest:
    def test_block_valid(self):
        req = BlockRequest(phone="5511999999999", action="block")
        assert req.action == "block"

    def test_unblock_valid(self):
        req = BlockRequest(phone="5511999999999", action="unblock")
        assert req.action == "unblock"

    def test_action_is_plain_string(self):
        """action is just a str field without enum validation."""
        req = BlockRequest(phone="5511999999999", action="invalid")
        assert req.action == "invalid"


# ═══════════════════════════════════════════════════════════════════════════
# WEBHOOK SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════

class TestWebhookCreateRequest:
    def test_minimal(self):
        req = WebhookCreateRequest(name="my hook", url="https://example.com/hook")
        assert req.active is True
        assert req.events == ["*"]
        assert req.method == "POST"

    def test_custom_events(self):
        req = WebhookCreateRequest(
            name="Text handler",
            url="https://example.com/text",
            events=["message.text"],
        )
        assert req.events == ["message.text"]

    def test_url_is_plain_string(self):
        """url is just a str field without URL validation."""
        req = WebhookCreateRequest(name="bad", url="not a url")
        assert req.url == "not a url"
