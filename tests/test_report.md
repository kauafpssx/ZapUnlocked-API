# ZapUnlocked-API Test Report

**Date:** 2026-06-16
**Test count:** 473 passed, 0 failures
**Status:** ✅ All green

---

## Test Suite Summary

| Metric | Value |
|---|---|
| Total tests | 473 |
| Passed | 473 |
| Failed | 0 |
| Test files | 37 |
| New test files (this session) | 8 |
| Source bugs fixed (all-time) | 8 |

---

## Test Files

### Core Utilities

| File | Tests | Description |
|---|---|---|
| `test_schemas.py` | 29 | Pydantic request/response schema validation |
| `test_json_cleaner.py` | 12 | `clean_json_text`, comment stripping, edge cases |
| `test_formatter.py` | 14 | Date/time placeholder replacement (`{{day}}`, `{{mon}}`, etc.) |
| `test_url_builder.py` | 4 | URL construction utilities |
| `test_callback_token.py` | 7 | HMAC callback token creation and verification |
| `test_decorators.py` | 7 | `@require_whatsapp`, `@handle_errors` FastAPI decorators |
| `test_vulture.py` | 1 | Dead code detection via `vulture --min-confidence 90` |
| `test_phone.py` ✨ | 8 | `resolve_jid()` — number→JID, group JID passthrough, `+`/space stripping |
| `test_dry_run.py` ✨ | 11 | `is_dry_run()`, `dry_run_response()`, `dry_run_media_response()` |
| `test_time.py` ✨ | 11 | `now_ts()`, `sent_response()`, `_resolve_tz_name()` — conf/env/UTC fallback |
| `test_constants.py` ✨ | 10 | `get_auth_dir()`, `get_data_dir()`, `_is_alwaysdata()` |
| `test_quote.py` ✨ | 13 | `resolve_quote()`, `build_send_options()` — found/stub/raise/combined |
| `test_constants.py` ✨ | 10 | `get_auth_dir()`, `get_data_dir()`, `_is_alwaysdata()` |

### WhatsApp State Management

| File | Tests | Description |
|---|---|---|
| `test_state_manager.py` | 16 | Thread-safe `WhatsAppState` singleton |
| `test_state_api.py` | 11 | Functional API getters/setters |
| `test_pairing_service.py` | 10 | Phone pairing code flow |

### WhatsApp Client & Lifecycle

| File | Tests | Description |
|---|---|---|
| `test_client.py` | 26 | `activate_qr`, `start_bot`, `logout`, `_intercept_pair_code`, `_patch_neonize_logging`, `_disconnect_existing`, `_configure_logging`, `_register_event_handlers`, `_load_db_config_and_start_scheduler` |

### Message Handling

| File | Tests | Description |
|---|---|---|
| `test_message_parser.py` | 16 | `parse_message` — conversation, extended text, captions, groups, LID, buttons, interactive, templates |
| `test_message_router.py` | 14 | `dispatch_message_event` — all message types, groups, reactions, deletions |
| `test_callback.py` | 10 | `handleMessage` — button callbacks, reactions, webhook dispatch, invalid tokens |
| `test_handler_helpers.py` | 14 | `_detect_type`, `get_contact_name`, `handle_message_async` |
| `test_message_fetcher.py` | 18 | `fetch_messages` — filtering, stubs, reactions, limits, non-dict handling; `get_recent_chats` |

### Event Handlers

| File | Tests | Description |
|---|---|---|
| `test_event_handlers.py` | 29 | All 20+ Neonize event callbacks — QR, connection lifecycle, pair code, messages, calls, presence, receipts, undecryptable, pictures, identity, group joins |

### Webhooks

| File | Tests | Description |
|---|---|---|
| `test_webhook_registry.py` | 21 | `create_webhook`, `list_webhooks`, `delete_webhook`, `toggle_webhook`, `get_active_webhooks_for_event`, wildcard `*` event support |
| `test_webhook_dispatcher.py` | 4 | Dispatch to registered webhooks |
| `test_webhook_service.py` | 4 | `trigger_webhook` — request sending, default payload, placeholder replacement |

### Media Processing

| File | Tests | Description |
|---|---|---|
| `test_media_utils.py` | 14 | `get_ffmpeg_path`, `warm_up_ffmpeg`, `run_ffmpeg_sync`, `cleanup`, `get_file_size` |
| `test_media_converters.py` | 18 | `convert_to_webp` (6 resize modes), `convert_to_mp4`, `convert_audio` (4 formats), error handling, duration extraction |
| `test_media_queue.py` | 3 | TaskQueue serialization |
| `test_downloader.py` | 9 | `download_media` — SSRF protection (private/loopback/link-local/multicast), content-type detection, size limits, extension fallback |

### Sessions

| File | Tests | Description |
|---|---|---|
| `test_session_registry.py` ✨ | 24 | `ensure_default_session`, `list_sessions`, `get_session`, `create_session`, `rename_session`, `delete_session`, `get_default_session_id`, `get_active_sessions` — SQLite CRUD |

### Middleware

| File | Tests | Description |
|---|---|---|
| `test_middleware.py` ✨ | 15 | `auth()` — API key via header/query, session_id resolution, 401 on bad key; `json_comment_stripper()` — comment/comma removal, passthrough on GET/non-JSON |

### Services

| File | Tests | Description |
|---|---|---|
| `test_stats.py` ✨ | 16 | `increment`, `get_all`, `increment_webhook`, `get_webhook_stats`, `reset`, `reset_webhook_stats` — per-session SQLite counters |
| `test_settings_service.py` | 5 | Settings file persistence and retrieval |
| `test_db_cleanup.py` | 6 | DB cleanup config, scheduler, interval management |
| `test_ip_rules_service.py` | 17 | IP whitelist/blacklist rules with SQLite persistence |
| `test_storage.py` | 22 | Chat index, message history (gzip), dedup, limits, clear |

---

## PELA Audit Results (2026-06-16)

### Static Analysis

| Category | Finding |
|---|---|
| Files audited | ~135 Python source files in `src/` |
| Syntax errors | 3 files with UTF-8 BOM (`\xef\xbb\xbf`) — Python handles these fine, but non-standard encoding |
| Dead code (≥90% confidence) | **0** — `test_vulture.py` enforces this on every run |
| Dead code (≥80% confidence) | **0** |

**Files with UTF-8 BOM (should be resaved as UTF-8 without BOM):**
- `src/controllers/status/getStatus.py`
- `src/controllers/status/readinessController.py`
- `src/controllers/status/statsController.py`

### Type Hint Coverage

| Metric | Value |
|---|---|
| Total functions | 490 |
| Return-typed functions | 275 (56.1%) |
| Annotated arguments | 683/830 (82.3%) |
| **Average type coverage** | **69.2%** |

### Cyclomatic Complexity (Top 10 — refactor candidates)

| CC | File | Function |
|---|---|---|
| 67 | `src/services/whatsapp/messageFetcher.py:5` | `fetch_messages()` |
| 45 | `src/handlers/message_router.py:12` | `dispatch_message_event()` |
| 38 | `src/utils/parsing/message_parser.py:8` | `parse_message()` |
| 33 | `src/controllers/whatsapp/send/sendButton.py:23` | `send_with_buttons()` |
| 30 | `src/controllers/status/logsController.py:81` | `get_logs()` |
| 25 | `src/services/whatsapp/sender/interactive.py:97` | `send_button_message()` |
| 23 | `src/services/media/resolver.py:28` | `resolve_media()` |
| 20 | `src/services/whatsapp/ai/chat.py:63` | `ask_meta_ai()` |
| 20 | `src/services/media/downloader.py:9` | `download_media()` |
| 19 | `src/services/whatsapp/event_handlers.py:490` | `handle_message_async()` |

> McCabe threshold = 10. Functions above 10 are refactor candidates. Functions above 20 are critical.

---

## Bugs Fixed (all-time)

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

## Features Verified

| Feature | Description |
|---|---|
| `message.deleted` | Webhook event triggered when a message is deleted (REVOKE). Verified via `test_message_router.py`. |
| `message.sent` | Webhook event triggered for all outgoing messages (text, media, buttons, etc.). |
| Multi-session | `session_id` propagated through auth middleware → controllers → services → SQLite. |
| DRY_RUN mode | `DRY_RUN=true` intercepts all sends and returns fake response without calling WhatsApp. |
| Callback tokens | HMAC-SHA256 button callbacks with 24h expiry, base64url-encoded, timing-safe compare. |

---

## Dead Code Removed (all-time)

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
- **SQLite isolation:** Tests use `temp_db` fixture (monkeypatches `DB_PATH` to `tmp_path`) for clean schema per test
- **File-based persistence:** Tests use `tmp_path` fixtures for isolated filesystem access (storage, webhook registry, IP rules, settings, db_cleanup)
- **Async tests:** `pytest-asyncio` with `asyncio_mode = auto`; `AsyncMock` for async dependencies
- **SSRF tests:** Mock `socket.gethostbyname` and `ipaddress.ip_address` to verify blocked IP ranges
- **Event handler tests:** Bypass `_run_in_loop` by patching with `side_effect = lambda fn: fn()` for synchronous execution
- **Dead code detection:** `test_vulture.py` runs `vulture src/ --min-confidence 90` and fails on any finding
- **AAA structure:** All tests follow Arrange / Act / Assert with blank-line separation

---

## Running the Tests

```bash
pytest              # Run all tests
pytest -v           # Verbose output
pytest --tb=long    # Full traceback on failures
pytest <file>       # Run a single test file
pytest -k <pattern> # Run tests matching a pattern
```
