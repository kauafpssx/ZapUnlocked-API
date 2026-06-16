# ZapUnlocked API — Structure & Patterns

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Python 3.13+ |
| Framework | FastAPI |
| WhatsApp | Neonize (Go bindings via whatsmeow) |
| Auth | API Key (header `x-api-key` ou query `?API_KEY=`) |
| Logs | Loguru (stdout + daily rotation) |
| Testes | pytest + pytest-asyncio |
| CI | GitHub Actions (lint + Docker build) |

---

## Architecture

```
HTTP Request
    ↓
auth.py (API Key validation + session_id resolution)
    ↓
ip_control.py (allow/block list)
    ↓
json_cleaner.py (strip comments from JSON body)
    ↓
Route (router.get/post/put/delete)
    ↓
Controller (recebe Request, chama Services, retorna dict)
    ↓
Service (business logic, sem HTTP)
    ↓
WhatsApp / Storage / Media / Webhook
```

---

## Code Patterns

### 1. Session ID flow

Autenticação resolve o `session_id` e injeta no `request.state`:

```python
# src/middleware/auth.py
session_id = (
    request.headers.get("X-Instance")
    or request.query_params.get("session")
    or get_default_session_id()  # "1"
)
request.state.session_id = session_id
```

Controllers acessam via:

```python
sid = getattr(request.state, "session_id", "1")
```

### 2. Controller pattern

Controllers são funções async que recebem `Request` + body e retornam `dict`:

```python
@router.post("/send")
async def send_message(request: Request, data: SendMessageSchema):
    sid = getattr(request.state, "session_id", "1")
    result = await send_text(sid, data.phone, data.message)
    return {"success": True, "data": result}
```

Erro padrão com `@handle_errors`:

```python
@router.post("/send_image")
@handle_errors("send image")
async def send_image(request: Request, ...):
    ...
```

### 3. Error response format

| Status | Formato |
|--------|---------|
| 200 | `{"success": true, ...}` |
| 400 | `{"error": "VALIDATION_ERROR", "message": "...", "details": [...]}` |
| 401 | `{"error": "UNAUTHORIZED", "message": "..."}` |
| 422 | `{"error": "VALIDATION_ERROR", "message": "...", "details": [...]}` |
| 500 | `{"error": "INTERNAL_ERROR", "message": "..."}` |
| 503 | `{"error": "WHATSAPP_NOT_CONNECTED", "message": "..."}` |

### 4. Dry run mode

Toda rota de send checa dry_run no topo:

```python
if is_dry_run():
    return {"success": True, "dry_run": True, "data": {...}}
```

### 5. WhatsApp state per session

Cada sessão tem um `WhatsAppState` isolado:

```
state_manager.py:  dict[str, WhatsAppState]  (thread-safe)
state.py:          wrapper funcional (get_client(sid), get_is_ready(sid), etc.)
```

---

## Route Examples

### Send text message

```
POST /send
x-api-key: <key>

{
    "phone": "5511999999999",
    "message": "Hello, world!"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "messageId": "3EB0ABCDEF123456",
        "timestamp": "2025-01-01T12:00:00Z"
    }
}
```

### Send image

```
POST /send_image
x-api-key: <key>

{
    "phone": "5511999999999",
    "image_url": "https://example.com/photo.jpg",
    "caption": "Look at this!"
}
```

### Send audio (auto-converted to PTT)

```
POST /send_audio
x-api-key: <key>

{
    "phone": "5511999999999",
    "audio_url": "https://example.com/audio.mp3"
}
```

### Interactive button

```
POST /messages/send-button-actions
x-api-key: <key>

{
    "phone": "5511999999999",
    "title": "Choose an option",
    "buttons": [
        {"id": "opt1", "text": "Option 1"},
        {"id": "opt2", "text": "Option 2"}
    ]
}
```

### Create webhook

```
POST /webhooks
x-api-key: <key>

{
    "name": "my-webhook",
    "url": "https://myapp.com/webhook",
    "events": ["message.text", "message.image"]
}

Response:
{
    "success": true,
    "webhook": {
        "name": "my-webhook",
        "url": "https://myapp.com/webhook",
        "active": true,
        "events": ["message.text", "message.image"]
    }
}
```

### Pair code

```
POST /session/pair
x-api-key: <key>

{
    "phone": "5511999999999"
}

Response:
{
    "success": true,
    "code": "NR62-NZSF",
    "expires_in_seconds": 120
}
```

---

## Project Structure

```
ZapUnlocked-API/
├── main.py                    # Entry point (thin — bootstrap + uvicorn)
├── requirements.txt
├── Dockerfile / docker-compose.yml
├── .env.example
│
├── src/
│   ├── app.py                 # FastAPI factory: middleware, routes, error handlers
│   ├── bootstrap.py           # Runtime boot: libmagic, deps, event loop policy
│   ├── lifespan.py            # Startup/shutdown: dirs, FFmpeg, WhatsApp bots
│   │
│   ├── routes/                # 12 routers — each maps to an API prefix
│   │   ├── index.py           # GET /, /status, /readiness
│   │   ├── send.py            # POST /send, /send_image, /send_audio...
│   │   ├── webhooks.py        # CRUD /webhooks
│   │   ├── system.py          # /system/env, /system/cleanup
│   │   ├── settings.py        # /settings/profile, /settings/privacy...
│   │   ├── qr.py              # /qr, /qr/image
│   │   ├── session.py         # /session/pair, /session/logout
│   │   ├── management.py      # /management/fetch_messages...
│   │   ├── contacts.py        # /contacts/info
│   │   ├── instance.py        # /instance/me, /instance/device
│   │   ├── ai.py              # /ai/chat
│   │   └── sessions_mgmt.py   # /sessions (multi-session CRUD)
│   │
│   ├── controllers/           # Request handlers (1 file ≈ 1 route)
│   │   ├── sessions/          # Session lifecycle
│   │   ├── status/            # Health, memory, volume, stats
│   │   ├── system/            # Env, cleanup, IP rules, export/import
│   │   ├── webhook/           # Webhook CRUD
│   │   └── whatsapp/
│   │       ├── send/          # ~19 files, one per message type
│   │       ├── qr/            # QR page, image, pair code, logout
│   │       ├── management/    # Chats, contacts, groups, DB
│   │       ├── settings/      # Profile, privacy, instance
│   │       ├── contacts/      # Block/unblock, contact info
│   │       └── ai/            # Meta AI chat
│   │
│   ├── services/              # Business logic (no HTTP dependency)
│   │   ├── media/             # Download, convert, validate, upload, cleanup
│   │   ├── sessions/          # Registry + migration
│   │   ├── webhooks/          # Registry, dispatcher, service, logs
│   │   └── whatsapp/          # Client, state, storage, sender/
│   │       └── sender/        # text, media, sticker, interactive, actions
│   │
│   ├── handlers/              # Internal message pipeline
│   │   ├── message_router.py  # Incoming message → webhook event
│   │   ├── callback.py        # Fire webhook callbacks
│   │   └── helpers.py         # Safe type coercions
│   │
│   ├── schemas/               # Pydantic models (send, settings, contacts, webhooks, ai)
│   ├── middleware/            # auth, ip_control, json_cleaner
│   ├── utils/                 # decorators, logger, formatter, phone, parsing, security
│   ├── views/                 # HTML templates (welcome + QR page)
│   └── static/                # Static assets
│
├── auth/                      # WhatsApp session SQLite files
├── data/                      # JSON persistence (sessions, stats, webhooks, ip_rules)
├── logs/                      # Rotated log files
├── temp_media/                # Auto-cleaned temp files
│
├── tests/                     # 30+ test files (one per module)
├── scripts/                   # Shell scripts (install, run, uninstall, generate-env)
│
└── docs/
    ├── STRUCTURE.md           # This file
    ├── webhook-events.md      # Full webhook event reference
    ├── knowledge/             # Neonize instance knowledge
    ├── translations/          # UI strings in 13 languages
    └── troubleshooting/       # Common errors
```

---

## Key Patterns

### Decorators

| Decorator | Onde usar | O que faz |
|-----------|-----------|-----------|
| `@require_whatsapp` | Send controllers | Retorna 503 se WhatsApp desconectado |
| `@handle_errors("name")` | All controllers | Captura exception, loga, retorna 500 |

### Service naming

- `services/whatsapp/` — tudo relacionado ao WhatsApp
- `services/media/` — pipeline de mídia
- `services/webhooks/` — engine de webhooks
- `services/*.py` — features independentes (stats, logs_cleanup, ip_rules_service)

### Storage

Tudo JSON file-based. Persistência em `data/`:

```
data/sessions.json        → src/services/sessions/registry.py
data/stats.json           → src/services/stats.py
data/ip_rules.json        → src/services/ip_rules_service.py
data/webhooks/*.json      → src/services/webhooks/registry.py
data/webhooks/*.logs.json → src/services/webhooks/logs.py
data/chats/*.json         → src/services/whatsapp/storage.py
```

### Webhook events

40+ eventos categorizados em:

| Grupo | Exemplos |
|-------|----------|
| `message.*` | text, image, video, audio, document, sticker, reaction, deleted |
| `connection.*` | connected, disconnected, qr_ready, pair_code, logged_out |
| `group.*` | join, update |
| `contact.*` | presence, chat_presence, picture_change, identity_change |
| `call.*` | received, accepted, terminated |

Cada webhook recebe:
```json
{
    "event": "message.text",
    "timestamp": "2025-01-01T12:00:00Z",
    "data": { "...": "..." }
}
```

### Session isolation

- Cada sessão tem seu próprio `auth/{id}/auth.sqlite`
- Cada sessão tem seu próprio `WhatsAppState` isolado
- Sessão padrão é `"1"`, definida em `sessions/registry.py`
- Header `X-Instance` ou query `?session=` para multi-session

---

## Testing

```
pytest.ini:
  testpaths = tests
  asyncio_mode = auto
  python_files = test_*.py

tests/
├── conftest.py     # Fixtures, mocks
├── test_*.py       # One file per module (30+ files)
```

**CI não executa testes** — atualmente só smoke test de import + Docker build.

---

## Logging

```python
# src/utils/logger.py — Loguru
logger.add(sys.stdout, level="DEBUG", format="...")   # Console colorido
logger.add("logs/zapunlocked_{time}.log",               # File with rotation
           rotation="1 day", retention="30 days", level="INFO")
```
