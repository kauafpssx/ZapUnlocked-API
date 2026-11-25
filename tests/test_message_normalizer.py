"""Tests for the canonical message normalizer (Fase 1).

Covers: PN/LID resolution, key/context extraction, native-flow preservation
(no id.isdigit()), order/product normalization, unknown types, malformed JSON,
safe serialization and secret redaction.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    InteractiveMessage,
    InteractiveResponseMessage,
    OrderMessage,
    ProductMessage,
)
from neonize.proto.Neonize_pb2 import MessageInfo, MessageSource, JID

from src.services.whatsapp.message_normalizer import (
    detect_type,
    normalize_context,
    normalize_message_event,
    normalize_message_key,
    normalize_native_flow_response,
    normalize_order,
    normalize_product,
    protobuf_to_safe_dict,
    resolve_chat_jid,
)


def _jid(user: str, server: str = "s.whatsapp.net") -> JID:
    return JID(User=user, Server=server, RawAgent=0, Device=0, Integrator=0)


def _source(
    chat_user="5511999999999",
    chat_server="s.whatsapp.net",
    is_group=False,
    is_from_me=False,
    sender_user=None,
    sender_server="s.whatsapp.net",
    sender_alt_user=None,
    sender_alt_server=None,
    recipient_alt_user=None,
    recipient_alt_server=None,
):
    return MessageSource(
        Chat=_jid(chat_user, chat_server),
        Sender=_jid(sender_user or chat_user, sender_server),
        SenderAlt=_jid(sender_alt_user or "", sender_alt_server or ""),
        RecipientAlt=_jid(recipient_alt_user or "", recipient_alt_server or ""),
        IsGroup=is_group,
        IsFromMe=is_from_me,
    )


def _info(source, msg_id="MSG1", pushname="Test User", timestamp=1_700_000_000):
    return MessageInfo(
        ID=msg_id,
        ServerID=0,
        Type="text",
        Pushname=pushname,
        Timestamp=timestamp,
        Category="direct",
        Multicast=False,
        MediaType="text",
        Edit="NONE",
        MessageSource=source,
    )


def _ev(message: Message, source=None, msg_id="MSG1", pushname="Test User"):
    src = source or _source()
    return SimpleNamespace(Info=_info(src, msg_id, pushname), Message=message)


# ── Type detection ───────────────────────────────────────────────────────────

class TestDetectType:
    def test_conversation(self):
        m = Message(conversation="hi")
        assert detect_type(m) == "conversation"

    def test_order(self):
        m = Message(orderMessage=OrderMessage(orderID="O1"))
        assert detect_type(m) == "orderMessage"

    def test_product(self):
        m = Message(productMessage=ProductMessage(body="x"))
        assert detect_type(m) == "productMessage"

    def test_interactive_response(self):
        r = InteractiveResponseMessage()
        r.nativeFlowResponseMessage.name = "quick_reply"
        m = Message(interactiveResponseMessage=r)
        assert detect_type(m) == "interactiveResponseMessage"

    def test_unknown(self):
        assert detect_type(Message()) == "unknown"


# ── JID / PN-LID resolution ──────────────────────────────────────────────────

class TestResolveChatJid:
    def test_direct_chat(self):
        assert resolve_chat_jid(_source()) == "5511999999999@s.whatsapp.net"

    def test_group_chat(self):
        src = _source(chat_user="120363000000000001", chat_server="g.us", is_group=True)
        assert resolve_chat_jid(src) == "120363000000000001@g.us"

    def test_bot_chat(self):
        src = _source(chat_user="867051314767696", chat_server="bot")
        assert resolve_chat_jid(src) == "867051314767696"

    def test_lid_resolves_sender_alt(self):
        src = _source(chat_server="lid", sender_alt_user="5511888888888", sender_alt_server="s.whatsapp.net")
        assert resolve_chat_jid(src) == "5511888888888@s.whatsapp.net"

    def test_lid_falls_back_to_recipient_alt(self):
        src = _source(chat_server="lid", recipient_alt_user="5511777777777", recipient_alt_server="s.whatsapp.net")
        assert resolve_chat_jid(src) == "5511777777777@s.whatsapp.net"

    def test_lid_falls_back_to_sender(self):
        src = _source(chat_server="lid", sender_user="5511666666666", sender_server="s.whatsapp.net")
        assert resolve_chat_jid(src) == "5511666666666@s.whatsapp.net"


# ── Key / context ────────────────────────────────────────────────────────────

class TestNormalizeKey:
    def test_key_fields(self):
        ev = _ev(Message(conversation="hi"), msg_id="ABC", pushname="Alice")
        key = normalize_message_key(ev.Info)
        assert key["id"] == "ABC"
        assert key["pushname"] == "Alice"
        assert key["chatJid"] == "5511999999999@s.whatsapp.net"
        assert key["fromMe"] is False

    def test_from_me_flag(self):
        src = _source(is_from_me=True)
        key = normalize_message_key(_info(src), )
        assert key["fromMe"] is True


class TestNormalizeContext:
    def test_quoted_message(self):
        m = Message()
        m.extendedTextMessage.text = "reply"
        m.extendedTextMessage.contextInfo.stanzaID = "QUOTED1"
        m.extendedTextMessage.contextInfo.mentionedJID.append("5511888888888")
        ctx = normalize_context(m)
        assert ctx["quotedMessageId"] == "QUOTED1"
        assert "5511888888888" in ctx["mentionedJids"]

    def test_no_context(self):
        m = Message(conversation="plain")
        ctx = normalize_context(m)
        assert ctx["quotedMessageId"] is None
        assert ctx["mentionedJids"] == []


# ── Native flow preservation (no id.isdigit) ─────────────────────────────────

class TestNativeFlow:
    def _resp(self, name="", params_json="", version=0):
        r = InteractiveResponseMessage()
        r.nativeFlowResponseMessage.name = name
        r.nativeFlowResponseMessage.version = version
        r.nativeFlowResponseMessage.paramsJSON = params_json
        return r

    def test_quick_reply_preserves_payload(self):
        flow = normalize_native_flow_response(
            self._resp("quick_reply", '{"id": "custom-id", "display_text": "OK"}', 1)
        )
        assert flow["name"] == "quick_reply"
        assert flow["version"] == 1
        assert flow["params"] == {"id": "custom-id", "display_text": "OK"}
        assert flow["kind"] == "button"
        assert flow["parseError"] is None

    def test_numeric_textual_id_still_button(self):
        # Old heuristic (id.isdigit) would call this a list — must be button now.
        flow = normalize_native_flow_response(
            self._resp("quick_reply", '{"id": "123", "display_text": "Row"}')
        )
        assert flow["kind"] == "button"

    def test_list_detected_by_name(self):
        flow = normalize_native_flow_response(
            self._resp("single_select", '{"id": "row_1"}')
        )
        assert flow["kind"] == "list"

    def test_list_detected_by_sections(self):
        flow = normalize_native_flow_response(
            self._resp("cta_see_options", '{"sections": []}')
        )
        assert flow["kind"] == "list"

    def test_form_detected(self):
        flow = normalize_native_flow_response(
            self._resp("galaxy_message", '{"field_1": "Kaua"}', 3)
        )
        assert flow["kind"] == "form"

    def test_malformed_json_preserves_raw(self):
        flow = normalize_native_flow_response(
            self._resp("quick_reply", "{not-json}")
        )
        assert flow["params"] is None
        assert flow["rawParamsJSON"] == "{not-json}"
        assert flow["parseError"] is not None


# ── Orders ───────────────────────────────────────────────────────────────────

class TestNormalizeOrder:
    def test_order_header(self):
        om = OrderMessage(
            orderID="ORDER1",
            itemCount=2,
            status=OrderMessage.INQUIRY,
            totalCurrencyCode="BRL",
            totalAmount1000=19900,
            orderTitle="Order #1",
            sellerJID="5511999990000@s.whatsapp.net",
        )
        om.token = "super-secret-token"
        order = normalize_order(om)
        assert order["orderId"] == "ORDER1"
        assert order["itemCount"] == 2
        assert order["statusName"] == "INQUIRY"
        assert order["totalAmount1000"] == 19900
        assert order["currency"] == "BRL"
        assert order["hasToken"] is True
        # Token value must never appear in the normalized output.
        assert "super-secret-token" not in str(order)

    def test_order_status_accepted(self):
        om = OrderMessage(orderID="O2", status=OrderMessage.ACCEPTED)
        assert normalize_order(om)["statusName"] == "ACCEPTED"


# ── Products ─────────────────────────────────────────────────────────────────

class TestNormalizeProduct:
    def test_product_snapshot(self):
        pm = ProductMessage(body="Check it", footer="Shop now")
        pm.product.productID = "P1"
        pm.product.title = "T-Shirt"
        pm.product.currencyCode = "BRL"
        pm.product.priceAmount1000 = 4990
        pm.catalog.title = "My Store"
        product = normalize_product(pm)
        assert product["body"] == "Check it"
        assert product["product"]["productId"] == "P1"
        assert product["product"]["priceAmount1000"] == 4990
        assert product["catalog"]["title"] == "My Store"


# ── Safe serialization / redaction ───────────────────────────────────────────

class TestProtobufToSafeDict:
    def test_redacts_token(self):
        om = OrderMessage(orderID="O1")
        om.token = "secret"
        d = protobuf_to_safe_dict(om)
        assert d.get("token") == "***REDACTED***"

    def test_none_returns_none(self):
        assert protobuf_to_safe_dict(None) is None

    def test_arbitrary_object(self):
        d = protobuf_to_safe_dict({"a": 1, "token": "x"})
        assert d["a"] == 1
        assert d["token"] == "***REDACTED***"


# ── Full envelope ────────────────────────────────────────────────────────────

class TestNormalizeMessageEvent:
    def test_text_envelope(self):
        ev = _ev(Message(conversation="hello"))
        env = normalize_message_event(ev, "5511999999999", session_id="1")
        assert env["event"] == "message.text"
        assert env["sessionId"] == "1"
        assert env["type"] == "conversation"
        assert env["data"]["text"] == "hello"
        assert env["chatJid"] == "5511999999999@s.whatsapp.net"

    def test_native_flow_envelope_event(self):
        r = InteractiveResponseMessage()
        r.nativeFlowResponseMessage.name = "quick_reply"
        r.nativeFlowResponseMessage.paramsJSON = '{"id": "ok"}'
        m = Message(interactiveResponseMessage=r)
        env = normalize_message_event(_ev(m), "5511999999999")
        assert env["event"] == "message.native_flow_response"
        assert env["data"]["kind"] == "button"

    def test_form_envelope_event(self):
        r = InteractiveResponseMessage()
        r.nativeFlowResponseMessage.name = "galaxy_message"
        r.nativeFlowResponseMessage.paramsJSON = '{"f": "1"}'
        m = Message(interactiveResponseMessage=r)
        env = normalize_message_event(_ev(m), "5511999999999")
        assert env["event"] == "message.form_response"

    def test_order_envelope_event(self):
        m = Message(orderMessage=OrderMessage(orderID="O1"))
        env = normalize_message_event(_ev(m), "5511999999999")
        assert env["event"] == "message.order_received"
        assert env["data"]["orderId"] == "O1"

    def test_product_envelope_event(self):
        m = Message(productMessage=ProductMessage(body="x"))
        env = normalize_message_event(_ev(m), "5511999999999")
        assert env["event"] == "message.product_received"

    def test_unknown_envelope(self):
        env = normalize_message_event(_ev(Message()), "5511999999999")
        assert env["event"] == "message.unknown"
        assert env["data"]["rawType"] == "unknown"

    def test_unknown_preserves_field_names(self):
        # senderKeyDistributionMessage is not in the type table → unknown w/ fields
        m = Message()
        m.senderKeyDistributionMessage.groupID = "123@g.us"
        env = normalize_message_event(_ev(m), "5511999999999")
        assert env["event"] == "message.unknown"
        assert "senderKeyDistributionMessage" in env["data"]["fields"]

    def test_session_and_sender_isolated(self):
        src = _source(sender_user="5511888888888")
        ev = _ev(Message(conversation="x"), source=src)
        env = normalize_message_event(ev, "5511999999999", session_id="2")
        assert env["sessionId"] == "2"
        assert env["senderJid"] == "5511888888888@s.whatsapp.net"
        assert env["chatJid"] == "5511999999999@s.whatsapp.net"