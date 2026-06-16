from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_neonize_client():
    with patch("src.services.whatsapp.client.NewClient") as mock:
        mock.return_value.connect = MagicMock()
        mock.return_value.disconnect = MagicMock()
        mock.return_value.logout = MagicMock()
        mock.return_value.qr = MagicMock()
        mock.return_value.event = MagicMock()
        yield mock


@pytest.fixture(autouse=True)
def mock_events():
    with patch("src.services.whatsapp.client.ConnectedEv") as m:
        yield m


class TestActivateQR:
    def test_noop_when_ready(self):
        with patch("src.services.whatsapp.client.state.get_is_ready", return_value=True):
            with patch("src.services.whatsapp.client.state.set_qr_generation_active") as mock_set:
                from src.services.whatsapp.client import activate_qr
                activate_qr()
                mock_set.assert_not_called()

    def test_activates_qr_generation(self):
        with patch("src.services.whatsapp.client.state.get_is_ready", return_value=False):
            with patch("src.services.whatsapp.client.state.set_qr_generation_active") as mock_set:
                from src.services.whatsapp.client import activate_qr
                activate_qr()
                mock_set.assert_called_once_with(True, None)

    def test_restarts_bot_if_qr_expired(self):
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        with patch("src.services.whatsapp.client.state.get_is_ready", return_value=False):
            with patch("src.services.whatsapp.client.state.get_qr", return_value=None):
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=mock_loop):
                    with patch("src.services.whatsapp.client.state.set_qr_generation_active") as mock_set:
                        with patch("src.services.whatsapp.client.state.set_keep_qr_active_on_restart") as mock_keep:
                            from src.services.whatsapp.client import activate_qr
                            activate_qr()
                            mock_set.assert_called_once_with(True, None)
                            mock_keep.assert_called_once_with(True, None)

    def test_does_not_restart_if_qr_active(self):
        with patch("src.services.whatsapp.client.state.get_is_ready", return_value=False):
            with patch("src.services.whatsapp.client.state.get_qr", return_value="data:image/png;base64,abc"):
                from src.services.whatsapp.client import activate_qr
                activate_qr()  # should not raise


class TestInterceptPairCode:
    def test_captures_valid_code(self):
        with patch("src.services.whatsapp.client.state.set_current_pair_code") as mock_set:
            from src.services.whatsapp.client import _intercept_pair_code
            _intercept_pair_code("Your pairing code is: ABCD-1234")
            mock_set.assert_called_once()
            code = mock_set.call_args[0][0]
            assert "ABCD-1234" in code

    def test_ignores_text_without_code(self):
        with patch("src.services.whatsapp.client.state.set_current_pair_code") as mock_set:
            from src.services.whatsapp.client import _intercept_pair_code
            _intercept_pair_code("Some other log message")
            mock_set.assert_not_called()

    def test_handles_code_without_dash(self):
        with patch("src.services.whatsapp.client.state.set_current_pair_code") as mock_set:
            from src.services.whatsapp.client import _intercept_pair_code
            _intercept_pair_code("code: ABCD1234 and more text")
            mock_set.assert_called_once()

    def test_replaces_space_with_dash(self):
        with patch("src.services.whatsapp.client.state.set_current_pair_code") as mock_set:
            from src.services.whatsapp.client import _intercept_pair_code
            _intercept_pair_code("Pair ABCD 5678")
            code = mock_set.call_args[0][0]
            assert "-" in code


class TestPatchNeonizeLogging:
    def test_patches_log_whatsmeow(self):
        mock_neonize_utils = type("FakeUtils", (), {"log_whatsmeow": lambda b, s: None})()
        mock_neonize_client = type("FakeClient", (), {"log_whatsmeow": lambda b, s: None})()

        with patch.dict("sys.modules", {
            "neonize.utils": mock_neonize_utils,
            "neonize.client": mock_neonize_client,
            "neonize.events": MagicMock(),
        }):
            from src.services.whatsapp.client import _patch_neonize_logging
            _patch_neonize_logging()
            assert mock_neonize_utils.log_whatsmeow is not None

    def test_patches_events_logger(self):
        mock_events = MagicMock()
        mock_events.log = MagicMock()
        mock_events.log._patched = False

        with patch.dict("sys.modules", {
            "neonize.utils": MagicMock(),
            "neonize.client": MagicMock(),
            "neonize.events": mock_events,
        }):
            from src.services.whatsapp.client import _patch_neonize_logging
            _patch_neonize_logging()
            assert mock_events.log.info is not None

    def test_handles_patch_failures_gracefully(self):
        with patch.dict("sys.modules", {
            "neonize.utils": MagicMock(spec=[]),
            "neonize.client": MagicMock(),
            "neonize.events": MagicMock(),
        }):
            from src.services.whatsapp.client import _patch_neonize_logging
            _patch_neonize_logging()  # should not raise


class TestStartBot:
    @pytest.fixture
    def mock_state(self):
        with patch("src.services.whatsapp.client.state") as mock:
            mock.get_client.return_value = None
            mock.get_main_loop.return_value = None
            mock.set_main_loop = MagicMock()
            mock.set_client = MagicMock()
            yield mock

    async def test_initializes_and_connects(self, mock_state, mock_neonize_client):
        with patch("src.services.whatsapp.client._reset_state") as mock_reset:
            with patch("src.services.whatsapp.client._disconnect_existing") as mock_disc:
                with patch("src.services.whatsapp.client._configure_logging") as mock_log:
                    with patch("src.services.whatsapp.client._patch_neonize_logging") as mock_patch:
                        with patch("src.services.whatsapp.client.cleanup_db") as mock_cleanup:
                            with patch("src.services.whatsapp.client._register_event_handlers") as mock_reg:
                                with patch("src.services.whatsapp.client._load_db_config_and_start_scheduler") as mock_sched:
                                    mock_loop = MagicMock()
                                    mock_loop.is_running.return_value = True

                                    from src.services.whatsapp.client import start_bot
                                    with patch("asyncio.get_running_loop", return_value=mock_loop):
                                        await start_bot()
                                        mock_reset.assert_called_once()
                                        mock_disc.assert_called_once()
                                        mock_log.assert_called_once()
                                        mock_patch.assert_called_once()
                                        mock_cleanup.assert_called_once()
                                        mock_reg.assert_called_once()
                                        mock_sched.assert_called_once()

    async def test_retries_on_error(self, mock_state, mock_neonize_client):
        with patch("src.services.whatsapp.client._reset_state") as mock_reset:
            with patch("src.services.whatsapp.client._disconnect_existing", side_effect=Exception("connection error")):
                with patch("src.services.whatsapp.client._configure_logging"):
                    with patch("src.services.whatsapp.client._patch_neonize_logging"):
                        with patch("src.services.whatsapp.client.cleanup_db"):
                            with patch("src.services.whatsapp.client._register_event_handlers"):
                                with patch("src.services.whatsapp.client._load_db_config_and_start_scheduler"):
                                    from src.services.whatsapp.client import start_bot
                                    with patch("asyncio.get_running_loop"):
                                        with patch("asyncio.sleep", new_callable=AsyncMock):
                                            with patch("asyncio.create_task") as mock_ct:
                                                await start_bot()
                                                mock_ct.assert_called_once()


class TestResetState:
    def test_resets_state(self):
        with patch("src.services.whatsapp.client.state.reset_for_reconnect") as mock_reset:
            from src.services.whatsapp.client import _reset_state
            _reset_state()
            mock_reset.assert_called_once()


class TestDisconnectExisting:
    def test_disconnects_existing_client(self):
        mock_client = MagicMock()
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            from src.services.whatsapp.client import _disconnect_existing
            _disconnect_existing()
            mock_client.disconnect.assert_called_once()

    def test_handles_no_client(self):
        with patch("src.services.whatsapp.client.state.get_client", return_value=None):
            from src.services.whatsapp.client import _disconnect_existing
            _disconnect_existing()  # should not raise

    def test_handles_disconnect_error(self):
        mock_client = MagicMock()
        mock_client.disconnect.side_effect = Exception("disconnect failed")
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            from src.services.whatsapp.client import _disconnect_existing
            _disconnect_existing()  # should not raise


class TestConfigureLogging:
    def test_sets_log_levels(self):
        with patch("src.services.whatsapp.client.neonize_logger.setLevel") as mock_set:
            with patch("src.services.whatsapp.client.logging.getLogger") as mock_get:
                from src.services.whatsapp.client import _configure_logging
                _configure_logging()
                mock_set.assert_called_once()
                mock_get.assert_called_once_with("whatsmeow")


class TestRegisterEventHandlers:
    def test_registers_all_handlers(self, mock_neonize_client, mock_events):
        fake_client = MagicMock()
        fake_client.event = MagicMock()
        with patch("src.services.whatsapp.client.state.get_client", return_value=fake_client):
            from src.services.whatsapp.client import _register_event_handlers
            _register_event_handlers()
            assert fake_client.qr.called
            assert fake_client.event.called

    def test_does_nothing_when_client_none(self):
        with patch("src.services.whatsapp.client.state.get_client", return_value=None):
            from src.services.whatsapp.client import _register_event_handlers
            _register_event_handlers()  # should not raise


class TestLoadDbConfig:
    def test_loads_config_and_starts_scheduler(self):
        with patch("src.services.whatsapp.client.load_db_config") as mock_load:
            with patch("src.services.whatsapp.client.db_cleanup_scheduler", new_callable=AsyncMock):
                with patch("asyncio.create_task") as mock_ct:
                    from src.services.whatsapp.client import _load_db_config_and_start_scheduler
                    _load_db_config_and_start_scheduler()
                    mock_load.assert_called_once()
                    mock_ct.assert_called_once()


class TestLogout:
    async def test_logout_disconnects_and_clears(self):
        mock_client = MagicMock()
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.client.state.reset_for_logout") as mock_reset:
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=None):
                    with patch("src.services.whatsapp.client.Path") as mock_path:
                        mock_path.return_value.exists.return_value = False
                        with patch("src.services.whatsapp.storage.clear_all_data", new_callable=AsyncMock) as mock_clear:
                            from src.services.whatsapp.client import logout
                            await logout(keep_data=False)
                            mock_client.logout.assert_called_once()
                            mock_client.disconnect.assert_called_once()
                            mock_reset.assert_called_once()
                            mock_clear.assert_called_once()

    async def test_logout_keeps_data(self):
        mock_client = MagicMock()
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.client.state.reset_for_logout"):
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=None):
                    with patch("src.services.whatsapp.client.Path"):
                        from src.services.whatsapp.client import logout
                        with patch("src.services.whatsapp.storage.clear_all_data", new_callable=AsyncMock) as mock_clear:
                            await logout(keep_data=True)
                            mock_clear.assert_not_called()

    async def test_logout_removes_auth_file(self, tmp_path):
        mock_client = MagicMock()
        auth_file = tmp_path / "auth.sqlite"
        auth_file.write_text("data")
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.client.state.reset_for_logout"):
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=None):
                    with patch("src.services.whatsapp.client.get_auth_dir", return_value=str(tmp_path)):
                        with patch("src.services.whatsapp.storage.clear_all_data", new_callable=AsyncMock):
                            from src.services.whatsapp.client import logout
                            await logout(keep_data=True)
                            assert not auth_file.exists()

    async def test_logout_restarts_bot(self):
        mock_client = MagicMock()
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        with patch("src.services.whatsapp.client.state.get_client", return_value=mock_client):
            with patch("src.services.whatsapp.client.state.reset_for_logout"):
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=mock_loop):
                    with patch("src.services.whatsapp.client.Path"):
                        with patch("src.services.whatsapp.storage.clear_all_data", new_callable=AsyncMock):
                            with patch("asyncio.sleep", new_callable=AsyncMock):
                                with patch("asyncio.create_task") as mock_ct:
                                    from src.services.whatsapp.client import logout
                                    await logout()
                                    mock_ct.assert_called()

    async def test_logout_handles_no_client(self):
        with patch("src.services.whatsapp.client.state.get_client", return_value=None):
            with patch("src.services.whatsapp.client.state.reset_for_logout"):
                with patch("src.services.whatsapp.client.state.get_main_loop", return_value=None):
                    with patch("src.services.whatsapp.client.Path"):
                        with patch("src.services.whatsapp.storage.clear_all_data", new_callable=AsyncMock):
                            from src.services.whatsapp.client import logout
                            await logout()  # should not raise
