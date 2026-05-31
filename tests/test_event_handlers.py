"""Tests for Neonize event callbacks — QR, connection lifecycle, messages, calls, etc."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.whatsapp.event_handlers import (
    _on_qr, _on_connected, _on_pair_code, _on_logged_out,
    _on_connect_failure, _on_stream_error, _on_temporary_ban,
    _on_client_outdated, _on_stream_replaced, _on_message,
    _on_history_sync, _on_call_offer, _on_undecryptable,
    _on_receipt, _on_presence, _on_chat_presence,
    _on_picture, _on_identity_change, _on_call_accept,
    _on_call_terminate, _on_joined_group, _on_pair_status,
)


def _get_fire_data(mock_fire):
    """Extract the data dict from _fire call."""
    return mock_fire.call_args[0][1]


def _get_fire_event(mock_fire):
    """Extract the event type string from _fire call."""
    return mock_fire.call_args[0][0]


@pytest.fixture(autouse=True)
def mock_run_in_loop():
    with patch("src.services.whatsapp.event_handlers._run_in_loop") as mock:
        mock.side_effect = lambda fn: fn()
        yield mock


@pytest.fixture(autouse=True)
def mock_state():
    with patch("src.services.whatsapp.event_handlers.state") as mock:
        mock.get_is_ready.return_value = False
        mock.get_qr.return_value = None
        mock.get_qr_generation_active.return_value = True
        mock.get_qr_url_logged.return_value = False
        mock.get_start_time.return_value = 100
        yield mock


@pytest.fixture(autouse=True)
def mock_fire():
    with patch("src.services.whatsapp.event_handlers._fire", new_callable=MagicMock) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_build_qr_url():
    with patch("src.services.whatsapp.event_handlers.build_qr_url", return_value="http://test/qr") as mock:
        yield mock


class TestQrHandler:
    def test_on_qr_sets_qr_and_fires_event(self, mock_state, mock_fire, mock_build_qr_url):
        c = MagicMock()
        _on_qr(c, b"qr_code_data_123")

        mock_state.set_current_qr.assert_called_once_with("qr_code_data_123")
        mock_state.set_qr_last_generated_at.assert_called_once()
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "connection.qr_ready"
        assert "qr" in _get_fire_data(mock_fire)

    def test_on_qr_skipped_when_already_connected(self, mock_state, mock_fire):
        mock_state.get_is_ready.return_value = True
        _on_qr(MagicMock(), b"data")
        mock_state.set_current_qr.assert_not_called()
        mock_fire.assert_not_called()

    def test_on_qr_logs_url_once(self, mock_state, mock_fire, mock_build_qr_url):
        mock_state.get_qr_url_logged.return_value = False
        _on_qr(MagicMock(), b"data")
        mock_state.set_qr_url_logged.assert_called_once_with(True)

    def test_on_qr_skipped_when_generation_inactive(self, mock_state, mock_fire):
        mock_state.get_qr_generation_active.return_value = False
        _on_qr(MagicMock(), b"data")
        mock_state.set_current_qr.assert_not_called()


class TestConnectionHandlers:
    def test_on_connected_marks_connected(self, mock_state, mock_fire):
        c = MagicMock()
        _on_connected(c, MagicMock())
        mock_state.mark_connected.assert_called_once()

    def test_on_connected_fires_with_phone(self, mock_state, mock_fire):
        c = MagicMock()
        c.get_me.return_value.JID.User = "5511999999999"
        _on_connected(c, MagicMock())
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "connection.connected"
        assert _get_fire_data(mock_fire)["phone"] == "5511999999999"

    def test_on_pair_code_not_connected_sets_code(self, mock_state, mock_fire):
        _on_pair_code(MagicMock(), "ABCD-1234", False)
        mock_state.set_current_pair_code.assert_called_once_with("ABCD-1234")
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "connection.pair_code"

    def test_on_pair_code_connected_fires_with_flag(self, mock_state, mock_fire):
        _on_pair_code(MagicMock(), "ABCD-1234", True)
        assert _get_fire_data(mock_fire)["connected"] is True

    def test_on_logged_out_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.Reason = "user_initiated"
        _on_logged_out(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "connection.logged_out"
        assert _get_fire_data(mock_fire)["reason"] == "user_initiated"

    def test_on_connect_failure_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.Reason = "timeout"
        ev.Message = "Connection timed out"
        _on_connect_failure(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "connection.connect_failure"
        assert _get_fire_data(mock_fire)["reason"] == "timeout"

    def test_on_stream_error_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.Code = 500
        _on_stream_error(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "connection.stream_error"
        assert _get_fire_data(mock_fire)["code"] == 500

    def test_on_temporary_ban_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.Code = "ban_123"
        ev.Expire = 3600
        _on_temporary_ban(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "connection.temporary_ban"
        assert _get_fire_data(mock_fire)["code"] == "ban_123"

    def test_on_client_outdated_fires_event(self, mock_fire):
        _on_client_outdated(MagicMock(), MagicMock())
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "connection.client_outdated"

    def test_on_stream_replaced_fires_event(self, mock_fire):
        _on_stream_replaced(MagicMock(), MagicMock())
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "connection.stream_replaced"

    def test_on_history_sync_noop(self, mock_state):
        _on_history_sync(MagicMock(), MagicMock())


class TestMessageHandler:
    def test_on_message_skips_old_messages(self, mock_state, mock_fire):
        msg = MagicMock()
        msg.Info.Timestamp = 50
        _on_message(MagicMock(), msg)
        mock_state.get_main_loop.assert_not_called()

    def test_on_message_schedules_when_loop_available(self, mock_state):
        loop = MagicMock()
        loop.is_running.return_value = True
        mock_state.get_main_loop.return_value = loop
        msg = MagicMock()
        msg.Info.Timestamp = 200
        _on_message(MagicMock(), msg)
        loop.call_soon_threadsafe.assert_called_once()

    def test_on_message_logs_warning_when_no_loop(self, mock_state):
        mock_state.get_main_loop.return_value = None
        msg = MagicMock()
        msg.Info.Timestamp = 200
        _on_message(MagicMock(), msg)


class TestCallHandlers:
    def test_on_call_offer_fires_event(self, mock_state, mock_fire):
        c = MagicMock()
        ev = MagicMock()
        meta = MagicMock()
        ev.basicCallMeta = meta
        meta.callID = "call_001"

        with patch("src.services.whatsapp.settingsService.get_settings",
                   return_value={"call_reject_auto": False}):
            with patch("neonize.utils.jid.Jid2String",
                       return_value="5511888888888@s.whatsapp.net"):
                _on_call_offer(c, ev)

        assert _get_fire_event(mock_fire) == "call.received"
        assert _get_fire_data(mock_fire)["callId"] == "call_001"

    def test_on_call_accept_fires_event(self, mock_fire):
        ev = MagicMock()
        meta = MagicMock()
        ev.basicCallMeta = meta
        meta.callID = "call_002"
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511888888888@s.whatsapp.net"):
            _on_call_accept(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "call.accepted"
        assert _get_fire_data(mock_fire)["callId"] == "call_002"

    def test_on_call_terminate_fires_event(self, mock_fire):
        ev = MagicMock()
        meta = MagicMock()
        ev.basicCallMeta = meta
        meta.callID = "call_003"
        ev.reason = "ended"
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511888888888@s.whatsapp.net"):
            _on_call_terminate(MagicMock(), ev)
        assert _get_fire_event(mock_fire) == "call.terminated"
        assert _get_fire_data(mock_fire)["reason"] == "ended"


class TestPresenceHandlers:
    def test_on_presence_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.From.User = "5511999999999"
        ev.From.Server = "s.whatsapp.net"
        ev.Unavailable = False
        ev.LastSeen = 0
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511999999999@s.whatsapp.net"):
            _on_presence(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["status"] == "online"

    def test_on_presence_unavailable_is_offline(self, mock_fire):
        ev = MagicMock()
        ev.From.User = "5511999999999"
        ev.From.Server = "s.whatsapp.net"
        ev.Unavailable = True
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511999999999@s.whatsapp.net"):
            _on_presence(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["status"] == "offline"


class TestMiscHandlers:
    def test_on_undecryptable_fires_event(self, mock_fire):
        ev = MagicMock()
        src = MagicMock()
        src.Chat.User = "5511999999999"
        src.Chat.Server = "s.whatsapp.net"
        src.IsGroup = False
        ev.Info.MessageSource = src
        _on_undecryptable(MagicMock(), ev)
        mock_fire.assert_called_once()
        assert _get_fire_event(mock_fire) == "message.undecryptable"

    def test_on_receipt_fires_event(self, mock_fire):
        ev = MagicMock()
        src = MagicMock()
        src.Chat.User = "5511999999999"
        src.Chat.Server = "s.whatsapp.net"
        src.IsGroup = False
        ev.MessageSource = src
        ev.MessageIDs = ["msg_1", "msg_2"]
        ev.Type = "read"
        ev.Timestamp = 1000
        _on_receipt(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["type"] == "read"
        assert _get_fire_data(mock_fire)["messageIds"] == ["msg_1", "msg_2"]

    def test_on_picture_removed(self, mock_fire):
        ev = MagicMock()
        ev.JID.User = "5511999999999"
        ev.JID.Server = "s.whatsapp.net"
        ev.Author = None
        ev.Remove = True
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511999999999@s.whatsapp.net"):
            _on_picture(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["action"] == "removed"

    def test_on_identity_change_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.JID.User = "5511999999999"
        ev.JID.Server = "s.whatsapp.net"
        ev.Implicit = True
        ev.Timestamp = 2000
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511999999999@s.whatsapp.net"):
            _on_identity_change(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["implicit"] is True

    def test_on_joined_group_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.GroupInfo.JID.User = "12345"
        ev.GroupInfo.JID.Server = "g.us"
        ev.GroupInfo.Name = "Test Group"
        ev.Reason = "invited"
        ev.Type = "group"
        with patch("neonize.utils.jid.Jid2String",
                   return_value="12345@g.us"):
            _on_joined_group(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["groupName"] == "Test Group"

    def test_on_pair_status_fires_event(self, mock_fire):
        ev = MagicMock()
        ev.ID.User = "5511999999999"
        ev.ID.Server = "s.whatsapp.net"
        ev.Status = "success"
        ev.BusinessName = "TestBiz"
        ev.Platform = "android"
        ev.Error = ""
        with patch("neonize.utils.jid.Jid2String",
                   return_value="5511999999999@s.whatsapp.net"):
            _on_pair_status(MagicMock(), ev)
        assert _get_fire_data(mock_fire)["businessName"] == "TestBiz"
