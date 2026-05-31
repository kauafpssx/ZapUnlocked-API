"""Tests for parse_message — the core neonize message → dict parser."""

from unittest.mock import MagicMock

import pytest

from src.utils.parsing.message_parser import parse_message


def _make_msg(
    user="5511999999999",
    server="s.whatsapp.net",
    is_group=False,
    is_from_me=False,
    conversation=None,
    extended_text=None,
    image_caption=None,
    button_text=None,
    button_id=None,
    interactive_params=None,
    stanza_id=None,
    quoted_message=None,
    sender_user=None,
    sender_server=None,
    sender_alt_user=None,
    sender_alt_server=None,
    recipient_alt_user=None,
    recipient_alt_server=None,
    protocol_type=None,
):
    msg = MagicMock()
    msg.Message = MagicMock()
    msg.Message.conversation = conversation

    info = MagicMock()
    info.ID = "ABC123"
    info.Pushname = "Test User"
    info.Timestamp = 1000000
    msg.Info = info

    source = MagicMock()
    source.Chat.User = user
    source.Chat.Server = server
    source.IsGroup = is_group
    source.IsFromMe = is_from_me
    source.Sender.User = sender_user or user
    source.Sender.Server = sender_server or server
    source.SenderAlt.User = sender_alt_user
    source.SenderAlt.Server = sender_alt_server
    source.RecipientAlt.User = recipient_alt_user
    source.RecipientAlt.Server = recipient_alt_server

    info.MessageSource = source

    if protocol_type is not None:
        msg.Message.protocolMessage = MagicMock()
        msg.Message.protocolMessage.type = protocol_type
    else:
        msg.Message.protocolMessage = MagicMock()
        del msg.Message.protocolMessage.type

    if extended_text is not None:
        msg.Message.extendedTextMessage = MagicMock()
        msg.Message.extendedTextMessage.text = extended_text
    else:
        msg.Message.extendedTextMessage = MagicMock()
        del msg.Message.extendedTextMessage.text

    if image_caption is not None:
        msg.Message.imageMessage = MagicMock()
        msg.Message.imageMessage.caption = image_caption
    else:
        msg.Message.imageMessage = MagicMock()
        del msg.Message.imageMessage.caption

    if button_text is not None or button_id is not None:
        msg.Message.buttonsResponseMessage = MagicMock()
        msg.Message.buttonsResponseMessage.selectedDisplayText = button_text
        msg.Message.buttonsResponseMessage.selectedButtonID = button_id
    else:
        msg.Message.buttonsResponseMessage = MagicMock()
        del msg.Message.buttonsResponseMessage.selectedDisplayText
        del msg.Message.buttonsResponseMessage.selectedButtonID

    if interactive_params is not None:
        native = MagicMock()
        native.paramsJSON = interactive_params
        msg.Message.interactiveResponseMessage = MagicMock()
        msg.Message.interactiveResponseMessage.nativeFlowResponseMessage = native
        msg.Message.interactiveResponseMessage.buttonResponseMessage = MagicMock()
        del msg.Message.interactiveResponseMessage.buttonResponseMessage.selectedButtonID
        del msg.Message.interactiveResponseMessage.buttonResponseMessage.selectedDisplayText
    else:
        msg.Message.interactiveResponseMessage = MagicMock()
        del msg.Message.interactiveResponseMessage.nativeFlowResponseMessage
        del msg.Message.interactiveResponseMessage.buttonResponseMessage

    # TemplateButtonReplyMessage - not set by default
    msg.Message.templateButtonReplyMessage = MagicMock()
    del msg.Message.templateButtonReplyMessage.selectedID
    del msg.Message.templateButtonReplyMessage.selectedDisplayText

    if stanza_id is not None:
        ctx = MagicMock()
        ctx.stanzaID = stanza_id
        ctx.quotedMessage = quoted_message
        msg.Message.extendedTextMessage.contextInfo = ctx
    else:
        ctx = MagicMock()
        del ctx.stanzaID
        msg.Message.extendedTextMessage.contextInfo = ctx

    return msg


class TestParseMessage:
    def test_none_message_returns_none(self):
        assert parse_message(None) is None

    def test_message_without_message_attr_returns_none(self):
        msg = MagicMock()
        msg.Message = None
        assert parse_message(msg) is None

    def test_simple_conversation(self):
        msg = _make_msg(conversation="Hello!")
        result = parse_message(msg)
        assert result["phone"] == "5511999999999"
        assert result["text"] == "Hello!"
        assert result["jid"] == "5511999999999@s.whatsapp.net"

    def test_extended_text_takes_priority(self):
        msg = _make_msg(conversation="fallback", extended_text="extended")
        result = parse_message(msg)
        assert result["text"] == "extended"

    def test_image_caption_takes_highest_priority(self):
        msg = _make_msg(
            conversation="conv",
            extended_text="ext",
            image_caption="caption",
        )
        result = parse_message(msg)
        assert result["text"] == "caption"

    def test_group_jid_suffix(self):
        msg = _make_msg(is_group=True, conversation="group msg")
        result = parse_message(msg)
        assert result["jid"] == "5511999999999@g.us"

    def test_lid_server_resolves_sender_alt(self):
        msg = _make_msg(
            server="lid",
            sender_alt_user="5511888888888",
            sender_alt_server="s.whatsapp.net",
            conversation="lid msg",
        )
        result = parse_message(msg)
        assert result["jid"] == "5511888888888@s.whatsapp.net"

    def test_lid_server_falls_back_to_recipient_alt(self):
        msg = _make_msg(
            server="lid",
            sender_alt_user=None,
            sender_alt_server=None,
            recipient_alt_user="5511777777777",
            recipient_alt_server="s.whatsapp.net",
            conversation="lid fallback",
        )
        result = parse_message(msg)
        assert result["jid"] == "5511777777777@s.whatsapp.net"

    def test_lid_server_falls_back_to_sender(self):
        msg = _make_msg(
            server="lid",
            sender_alt_user=None,
            sender_alt_server=None,
            recipient_alt_user=None,
            recipient_alt_server=None,
            sender_user="5511666666666",
            sender_server="s.whatsapp.net",
            conversation="lid sender fallback",
        )
        result = parse_message(msg)
        assert result["jid"] == "5511666666666@s.whatsapp.net"

    def test_button_response_captured(self):
        msg = _make_msg(
            conversation="btn text",
            button_text="Option 1",
            button_id="btn_123",
        )
        result = parse_message(msg)
        assert result["buttonResponse"] == "btn_123"

    def test_interactive_response_native_flow(self):
        msg = _make_msg(
            conversation="interactive",
            interactive_params='{"id": "row_42", "display_text": "Row Title"}',
        )
        result = parse_message(msg)
        assert result["buttonResponse"] == "row_42"

    def test_interactive_response_button_msg(self):
        msg = _make_msg(conversation="interactive btn")
        msg.Message.interactiveResponseMessage.nativeFlowResponseMessage = None

        btn = MagicMock()
        btn.selectedButtonID = "btn_99"
        btn.selectedDisplayText = "Button 99"
        msg.Message.interactiveResponseMessage.buttonResponseMessage = btn

        result = parse_message(msg)
        assert result["buttonResponse"] == "btn_99"

    def test_quoted_message_captured(self):
        quoted = MagicMock()
        quoted.someField = "quoted data"
        msg = _make_msg(
            conversation="reply",
            stanza_id="stanza_001",
            quoted_message=quoted,
        )
        result = parse_message(msg)
        assert result["quotedMessage"] is quoted

    def test_empty_text_falls_through(self):
        msg = _make_msg(conversation="")
        result = parse_message(msg)
        assert result["text"] == ""


class TestParseMessageEdgeCases:
    def test_missing_attributes_do_not_crash(self):
        msg = MagicMock()
        msg.Message = MagicMock()
        msg.Message.conversation = "hi"
        info = MagicMock()
        info.ID = "ID"
        source = MagicMock()
        source.Chat.User = "5511999999999"
        source.Chat.Server = "s.whatsapp.net"
        source.IsGroup = False
        source.IsFromMe = False
        source.Sender = MagicMock()
        source.Sender.User = "5511999999999"
        source.Sender.Server = "s.whatsapp.net"
        source.SenderAlt = MagicMock()
        del source.SenderAlt.User
        del source.SenderAlt.Server
        source.RecipientAlt = MagicMock()
        del source.RecipientAlt.User
        del source.RecipientAlt.Server
        info.MessageSource = source
        msg.Info = info

        result = parse_message(msg)
        assert result is not None
        assert result["phone"] == "5511999999999"

    def test_accessing_nested_optional_fields_safe(self):
        msg = MagicMock()
        msg.Message = MagicMock()
        msg.Message.conversation = "safe text"
        info = MagicMock()
        info.ID = "ID"
        source = MagicMock()
        source.Chat.User = "5511999999999"
        source.Chat.Server = "s.whatsapp.net"
        source.IsGroup = False
        source.IsFromMe = False
        source.Sender = MagicMock()
        source.Sender.User = "5511999999999"
        source.Sender.Server = "s.whatsapp.net"
        source.SenderAlt = MagicMock()
        del source.SenderAlt.User
        del source.SenderAlt.Server
        source.RecipientAlt = MagicMock()
        del source.RecipientAlt.User
        del source.RecipientAlt.Server
        info.MessageSource = source
        msg.Info = info

        for attr in ["extendedTextMessage", "imageMessage", "buttonsResponseMessage",
                      "interactiveResponseMessage"]:
            sub = MagicMock()
            del sub.text
            del sub.caption
            del sub.selectedDisplayText
            del sub.selectedButtonID
            del sub.nativeFlowResponseMessage
            del sub.buttonResponseMessage
            setattr(msg.Message, attr, sub)

        tbr = MagicMock()
        del tbr.selectedID
        del tbr.selectedDisplayText
        msg.Message.templateButtonReplyMessage = tbr

        result = parse_message(msg)
        assert result["text"] == "safe text"
