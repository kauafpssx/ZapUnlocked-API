"""Tests for dispatch_message_event — message type routing and webhook dispatching."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.message_router import dispatch_message_event


def _make_msg(
    user="5511999999999",
    server="s.whatsapp.net",
    is_group=False,
    is_from_me=False,
    msg_id="MSG001",
    push_name="Test User",
    **fields,
):
    msg = MagicMock()
    msg.Message = MagicMock(spec=[])
    msg.Message.conversation = None

    info = MagicMock()
    info.ID = msg_id
    info.Pushname = push_name
    info.Timestamp = 2000000
    msg.Info = info

    source = MagicMock()
    source.Chat.User = user
    source.Chat.Server = server
    source.IsGroup = is_group
    source.IsFromMe = is_from_me
    info.MessageSource = source

    for field_name, field_value in fields.items():
        if isinstance(field_value, dict):
            sub = MagicMock(spec=[])
            for k, v in field_value.items():
                setattr(sub, k, v)
            setattr(msg.Message, field_name, sub)
        else:
            setattr(msg.Message, field_name, field_value)

    return msg


class TestDispatchMessageEvent:
    @pytest.fixture(autouse=True)
    def mock_dispatch_event(self):
        with patch(
            "src.services.webhooks.dispatcher.dispatch_event",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    async def test_text_message_from_conversation(self, mock_dispatch_event):
        msg = _make_msg(conversation="Hello world")
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        mock_dispatch_event.assert_awaited_once()
        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.text"
        assert args[1]["text"] == "Hello world"
        assert args[1]["from"] == "5511999999999"
        assert args[1]["messageId"] == "MSG001"
        assert args[1]["isGroup"] is False

    async def test_text_message_from_extended(self, mock_dispatch_event):
        msg = _make_msg(
            conversation="",
            extendedTextMessage={"text": "Extended text"},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.text"
        assert args[1]["text"] == "Extended text"

    async def test_text_with_quoted(self, mock_dispatch_event):
        ext = MagicMock(spec=[])
        ext.text = "Quoting"
        ctx = MagicMock(spec=[])
        ctx.stanzaID = "STANZA1"
        ctx.remoteJid = "5511999999999@s.whatsapp.net"
        ext.contextInfo = ctx
        msg = _make_msg(
            conversation="",
            extendedTextMessage=ext,
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.text"
        assert args[1]["quoted"]["id"] == "STANZA1"

    async def test_image_message(self, mock_dispatch_event):
        msg = _make_msg(
            imageMessage={"caption": "Photo!", "mimetype": "image/jpeg", "fileLength": 12345},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.image"
        assert args[1]["caption"] == "Photo!"
        assert args[1]["mimeType"] == "image/jpeg"

    async def test_video_message(self, mock_dispatch_event):
        msg = _make_msg(
            videoMessage={"mimetype": "video/mp4", "fileLength": 99999, "PTT": False, "gifPlayback": True},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.video"
        assert args[1]["isGif"] is True

    async def test_audio_message(self, mock_dispatch_event):
        msg = _make_msg(
            audioMessage={"mimetype": "audio/ogg", "fileLength": 5000, "PTT": True, "seconds": 30},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.audio"
        assert args[1]["isPTT"] is True
        assert args[1]["durationSeconds"] == 30

    async def test_document_message(self, mock_dispatch_event):
        msg = _make_msg(
            documentMessage={"fileName": "report.pdf", "mimetype": "application/pdf", "fileLength": 55555},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.document"
        assert args[1]["fileName"] == "report.pdf"

    async def test_sticker_message(self, mock_dispatch_event):
        msg = _make_msg(
            stickerMessage={"mimetype": "image/webp", "isAnimated": True},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.sticker"
        assert args[1]["isAnimated"] is True

    async def test_contact_message(self, mock_dispatch_event):
        msg = _make_msg(
            contactMessage={"displayName": "John", "vcard": "BEGIN:VCARD..."},
        )
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.contact"
        assert args[1]["displayName"] == "John"

    async def test_location_message(self, mock_dispatch_event):
        loc = MagicMock(spec=[])
        loc.degreesLatitude = -23.5505
        loc.degreesLongitude = -46.6333
        loc.name = "São Paulo"
        loc.address = "SP, Brazil"
        msg = _make_msg(locationMessage=loc)
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.location"
        assert args[1]["lat"] == -23.5505

    async def test_reaction_message(self, mock_dispatch_event):
        key = MagicMock(spec=[])
        key.ID = "TARGET_MSG"
        react = MagicMock(spec=[])
        react.text = "❤️"
        react.key = key
        msg = _make_msg(reactionMessage=react)
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.reaction"
        assert args[1]["emoji"] == "❤️"
        assert args[1]["targetMessageId"] == "TARGET_MSG"

    async def test_protocol_message_revoke(self, mock_dispatch_event):
        key = MagicMock(spec=[])
        key.ID = "DELETED_MSG"
        pm = MagicMock(spec=[])
        pm.type = 0  # REVOKE
        pm.key = key
        msg = _make_msg(protocolMessage=pm)
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.deleted"
        assert args[1]["targetMessageId"] == "DELETED_MSG"

    async def test_unknown_message_type(self, mock_dispatch_event):
        msg = _make_msg()
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@s.whatsapp.net"})

        args, _ = mock_dispatch_event.call_args
        assert args[0] == "message.unknown"

    async def test_group_message_sets_is_group_true(self, mock_dispatch_event):
        msg = _make_msg(is_group=True, conversation="Group chat")
        await dispatch_message_event(msg, "5511999999999", {"jid": "5511999999999@g.us"})

        args, _ = mock_dispatch_event.call_args
        assert args[1]["isGroup"] is True
