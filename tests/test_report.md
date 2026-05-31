# ZapUnlocked-API Test Report

**Date:** 2026-05-31
**Test count:** 361 passed, 0 failures
**Status:** ✅ All green

---

## Test Suite Summary

| Metric | Value |
|---|---|
| Total tests | 361 |
| Passed | 361 |
| Failed | 0 |
| Test files | 29 |
| Source bugs fixed | 8 |

---

## Test Files

### Core Utilities

| File | Tests | Description |
|---|---|---|
| `test_schemas.py` | 29 | Pydantic request/response schema validation |
| `test_json_cleaner.py` | 12 | `clean_json_text`, comment stripping, edge cases |
| `test_formatter.py` | 14 | Phone number formatting and validation |
| `test_url_builder.py` | 4 | URL construction utilities |
| `test_callback_token.py` | 7 | HMAC callback token creation and verification |
| `test_decorators.py` | 7 | `@require_whatsapp`, `@handle_errors` FastAPI decorators |
| `test_vulture.py` | 1 | Dead code detection via `vulture --min-confidence 90` |

### WhatsApp State Management

| File | Tests | Description |
|---|---|---|
| `test_state_manager.py` | 16 | Thread-safe `WhatsAppState` singleton |
| `test_state_api.py` | 10 | Functional API getters/setters |
| `test_pairing_service.py` | 10 | Phone pairing code flow |

### WhatsApp Client & Lifecycle

| File | Tests | Description |
|---|---|---|
| `test_client.py` | 28 | `activate_qr`, `start_bot`, `logout`, `_intercept_pair_code`, `_patch_neonize_logging`, `_disconnect_existing`, `_configure_logging`, `_register_event_handlers`, `_load_db_config_and_start_scheduler` |

### Message Handling

| File | Tests | Description |
|---|---|---|
| `test_message_parser.py` | 16 | `parse_message` — conversation, extended text, captions, groups, LID, buttons, interactive, templates |
| `test_message_router.py` | 14 | `dispatch_message_event` — all message types, groups, reactions, deletions |
| `test_callback.py` | 10 | `handleMessage` — button callbacks, reactions, webhook dispatch, invalid tokens |
| `test_handler_helpers.py` | 14 | `_detect_type`, `get_contact_name`, `handle_message_async` |
| `test_message_fetcher.py` | 16 | `fetch_messages` — filtering, stubs, reactions, limits, non-dict handling; `get_recent_chats` |

### Event Handlers

| File | Tests | Description |
|---|---|---|
| `test_event_handlers.py` | 29 | All 20+ Neonize event callbacks — QR, connection lifecycle, pair code, messages, calls, presence, receipts, undecryptable, pictures, identity, group joins |

### Webhooks

| File | Tests | Description |
|---|---|---|
| `test_webhook_registry.py` | 21 | `register_webhook`, `list_webhooks`, `remove_webhook`, file-based persistence |
| `test_webhook_dispatcher.py` | 4 | Dispatch to registered webhooks |
| `test_webhook_service.py` | 4 | `trigger_webhook` — request sending, default payload, placeholder replacement |

### Media Processing

| File | Tests | Description |
|---|---|---|
| `test_media_utils.py` | 13 | `get_ffmpeg_path`, `warm_up_ffmpeg`, `run_ffmpeg_sync`, `cleanup`, `get_file_size` |
| `test_media_converters.py` | 17 | `convert_to_webp` (6 resize modes), `convert_to_mp4`, `convert_audio` (4 formats), error handling, duration extraction |
| `test_media_queue.py` | 3 | TaskQueue serialization |
| `test_downloader.py` | 9 | `download_media` — SSRF protection (private/loopback/link-local/multicast), content-type detection, size limits, extension fallback |

### Services

| File | Tests | Description |
|---|---|---|
| `test_settings_service.py` | 5 | Settings file persistence and retrieval |
| `test_db_cleanup.py` | 6 | DB cleanup config, scheduler, interval management |
| `test_ip_rules_service.py` | 17 | IP whitelist/blacklist rules with file persistence |
| `test_storage.py` | 22 | Chat index, message history (gzip), dedup, limits, clear |

---

## Bugs Fixed

| File | Issue |
|---|---|
| `messageFetcher.py:57` | Lambda had unused `ts` parameter not passed in call — caused `TypeError` when processing stub messages |
| `sendLink.py:20` | `AnyUrl` type too strict for non-URL button IDs; changed to `str` |
| `actions.py:172` | `delete_message` sender JID used wrong user; fixed to `client.get_me().JID` |
| `actions.py:194` | `mark_read` called with wrong neonize API signature (keyword-only) |
| `queue.py:23` | Traceback spam on `getattr` for non-dict task items |
| `event_handlers.py:302` | Receipt events not split by type; created `message.delivered` (type 1), `message.read` (type 4), `message.receipt` (others) |
| `state.py/db_cleanup.py` | 2 pre-existing state singleton isolation failures fixed: `load_db_config()` resets globals when no file exists; `reset_for_logout()` resets `_main_loop` |
| `interactive.py` | Android buttons not appearing (removed `viewOnceMessage` wrapper, `messageVersion=3`, `add_msg_secret=True`) and button response not detected (`templateButtonReplyMessage` field not in parser/router) |

---

## New Features Verified

| Feature | Description |
|---|---|
| `message.deleted` | Webhook event triggered when a message is deleted (REVOKE). Verified via `test_message_router.py`. |
| `message.sent` | Webhook event triggered for all outgoing messages (text, media, buttons, etc.). |

---

## Dead Code Removed

| Item | Type |
|---|---|
| `getMemoryStats.py` import `get_store` | Unused import |
| `instanceController.py` import `PairPhoneRequest` | Unused import |
| `client.py` imports `get_pair_code`, `reset_pair_code`, `get_store`, `get_contact_name` | Unused imports |
| `interactive.py` import `PollCreationMessage` | Unused import |
| `state.py` functions `get_pair_code()`, `reset_pair_code()`, `get_store()` | Dead functions |
| `event_handlers.py` function `get_contact_name()` | Dead function |
| `audioConverter.py` function `convert_audio_for_ios()` | Dead function |
| `utils.py` function `get_ffprobe_path()` + global `_ffprobe_path` | Dead function + global |
| `storage.py` functions `bulk_add_messages()`, `resolve_phone_from_jid()`, `update_message_reaction()` | Dead functions |
| `stickerMetadata.py` | Entire file (dead) |
| `schemas/webhooks.py` classes `WebhookConfigIn`, `WebhookToggleIn` | Dead schemas |
| `schemas/settings.py` class `PairPhoneRequest` | Dead schema |
| `constants.py` constant `WHATSAPP_CONFIG` | Dead constant |
| `state_manager.py` attribute `_lock` | Dead attribute |
| `__init__.py` exports `get_store`, `get_pair_code`, `reset_pair_code` | Dead lazy exports |
| `schemas/__init__.py` exports `WebhookConfigIn`, `WebhookToggleIn`, `PairPhoneRequest` | Dead re-exports |

---

## Key Test Patterns

- **Mocking strategy:** `unittest.mock.patch` for external dependencies (neonize, subprocess, requests, filesystem)
- **Neonize imports:** Enabled in tests via `conftest.py` adding the libmagic DLL directory to `PATH`
- **File-based persistence:** Tests use `tmp_path` fixtures for isolated filesystem access (storage, webhook registry, IP rules, settings, db_cleanup)
- **Async tests:** `pytest-asyncio` with `asyncio_mode = auto`; `AsyncMock` for async dependencies
- **SSRF tests:** Mock `socket.gethostbyname` and `ipaddress.ip_address` to verify blocked IP ranges
- **Event handler tests:** Bypass `_run_in_loop` by patching with `side_effect = lambda fn: fn()` for synchronous execution
- **Dead code detection:** `test_vulture.py` runs `vulture src/ --min-confidence 90` and fails on any finding

---

## Running the Tests

```bash
pytest              # Run all tests
pytest -v           # Verbose output
pytest --tb=long    # Full traceback on failures
pytest <file>       # Run a single test file
pytest -k <pattern> # Run tests matching a pattern
```
