# Webhook Events — ZapUnlocked API

All webhooks receive a standard envelope:

```json
{
  "event": "message.text",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": { ... }
}
```

If the webhook has a custom `body` configured with `{{placeholders}}`, that custom body is sent instead of the standard envelope.

---

## Management

| Route | Description |
|-------|-------------|
| `GET /webhooks` | List all webhooks |
| `POST /webhooks` | Create a webhook |
| `GET /webhooks/{name}` | Get webhook details |
| `PUT /webhooks/{name}` | Update webhook |
| `DELETE /webhooks/{name}` | Delete webhook |
| `POST /webhooks/{name}/toggle` | Enable / disable |
| `POST /webhooks/{name}/test` | Send test payload |
| `GET /webhooks/events` | List all available event types |

### Create webhook — Example

```json
POST /webhooks
{
  "name": "my-crm",
  "url": "https://mycrm.com/hook",
  "events": ["message.text", "message.button_reply"],
  "active": true
}
```

Use `"events": ["*"]` to receive all event types.

---

## Incoming Message Events

All incoming message events share these base fields in `data`:

```json
{
  "messageId": "3EB0ABCDEF123456",
  "from": "5511999999999",
  "fromName": "John Doe",
  "fromJid": "5511999999999@s.whatsapp.net",
  "isGroup": false
}
```

---

### `message.text`

Plain or formatted text message.

```json
{
  "event": "message.text",
  "data": {
    "messageId": "...",
    "from": "5511999999999",
    "fromName": "John",
    "fromJid": "5511999999999@s.whatsapp.net",
    "isGroup": false,
    "text": "Hello! How can I help you?",
    "quoted": {
      "id": "3EB0...",
      "fromMe": true
    }
  }
}
```

`quoted` is `null` when not a reply.

---

### `message.image`

```json
{
  "event": "message.image",
  "data": {
    "...base": "...",
    "caption": "Product photo",
    "mimetype": "image/jpeg",
    "fileLength": 204800
  }
}
```

---

### `message.video`

```json
{
  "event": "message.video",
  "data": {
    "...base": "...",
    "caption": "Check out this video!",
    "mimetype": "video/mp4",
    "fileLength": 5242880,
    "isPTT": false,
    "isGif": false
  }
}
```

---

### `message.audio`

```json
{
  "event": "message.audio",
  "data": {
    "...base": "...",
    "mimetype": "audio/ogg; codecs=opus",
    "fileLength": 30720,
    "isPTT": true,
    "durationSeconds": 8
  }
}
```

`isPTT: true` = voice note recorded on WhatsApp.

---

### `message.document`

```json
{
  "event": "message.document",
  "data": {
    "...base": "...",
    "fileName": "contract.pdf",
    "caption": "Please find the contract attached",
    "mimetype": "application/pdf",
    "fileLength": 102400
  }
}
```

---

### `message.sticker`

```json
{
  "event": "message.sticker",
  "data": {
    "...base": "...",
    "mimetype": "image/webp",
    "isAnimated": false
  }
}
```

---

### `message.contact`

Shared contact.

```json
{
  "event": "message.contact",
  "data": {
    "...base": "...",
    "displayName": "Maria Souza",
    "vcard": "BEGIN:VCARD\nVERSION:3.0\n..."
  }
}
```

---

### `message.contacts`

Multiple contacts shared at once.

```json
{
  "event": "message.contacts",
  "data": {
    "...base": "...",
    "displayName": "2 contacts",
    "count": 2,
    "contacts": [
      { "displayName": "Maria Souza", "vcard": "BEGIN:VCARD\n..." },
      { "displayName": "João Silva", "vcard": "BEGIN:VCARD\n..." }
    ]
  }
}
```

---

### `message.location`

```json
{
  "event": "message.location",
  "data": {
    "...base": "...",
    "lat": -23.5505,
    "lng": -46.6333,
    "name": "Av. Paulista",
    "address": "Av. Paulista, 1000 — São Paulo"
  }
}
```

---

### `message.reaction`

Emoji reaction to a message.

```json
{
  "event": "message.reaction",
  "data": {
    "...base": "...",
    "emoji": "❤️",
    "targetMessageId": "3EB0ABCDEF123456",
    "isRemoved": false
  }
}
```

`isRemoved: true` when the user **removes** the reaction (empty emoji).

---

### `message.poll_created`

Poll received.

```json
{
  "event": "message.poll_created",
  "data": {
    "...base": "...",
    "pollName": "What's the best flavor?",
    "options": ["Chocolate", "Strawberry", "Vanilla"]
  }
}
```

---

### `message.poll_vote`

Vote on a poll.

```json
{
  "event": "message.poll_vote",
  "data": {
    "...base": "...",
    "pollId": "3EB0ABCDEF123456",
    "selectedOptions": ["Chocolate"]
  }
}
```

---

### `message.button_reply`

Button click (quick_reply, cta_url, cta_copy, etc.).

```json
{
  "event": "message.button_reply",
  "data": {
    "...base": "...",
    "buttonId": "option_yes",
    "displayText": "Yes",
    "type": "quick_reply"
  }
}
```

`type` can be `quick_reply` (modern button) or `legacy_button` (older format).

---

### `message.list_reply`

Selection from an interactive list.

```json
{
  "event": "message.list_reply",
  "data": {
    "...base": "...",
    "rowId": "1",
    "title": "X-Burger",
    "description": "$ 18.90"
  }
}
```

---

### `message.deleted`

Message deleted by the sender.

```json
{
  "event": "message.deleted",
  "data": {
    "...base": "..."
  }
}
```

---

### `message.unknown`

Unmapped message type.

```json
{
  "event": "message.unknown",
  "data": {
    "...base": "...",
    "rawType": "senderKeyDistributionMessage"
  }
}
```

---

### `message.undecryptable`

Message that could not be decrypted.

```json
{
  "event": "message.undecryptable",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net"
  }
}
```

---

## Sent Message Events

### `message.sent`

Fired after every outgoing message, regardless of type.

```json
{
  "event": "message.sent",
  "data": {
    "to": "5511999999999",
    "type": "text",
    "messageId": "3EB0ABCDEF123456"
  }
}
```

`type` values: `text`, `image`, `audio`, `video`, `document`, `sticker`, `gif`, `interactive`, `poll`, `location`, `contact`, `contacts`, `link`, `reaction`, `edit`, `delete`.

---

### `message.sent.{type}`

Same payload as `message.sent`, but with a specific event name per type. Useful when you only want to subscribe to a single outgoing message type.

```
message.sent.text
message.sent.image
message.sent.audio
message.sent.video
message.sent.document
message.sent.sticker
message.sent.gif
message.sent.interactive
message.sent.poll
message.sent.location
message.sent.contact
message.sent.link
message.sent.reaction
```

Example:

```json
{
  "event": "message.sent.image",
  "data": {
    "to": "5511999999999",
    "type": "image",
    "messageId": "3EB0ABCDEF123456"
  }
}
```

---

### `message.delivered`

Message delivered to the recipient's device.

```json
{
  "event": "message.delivered",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "messageIds": ["3EB0ABCDEF123456"],
    "type": 1,
    "timestamp": 1704067200
  }
}
```

---

### `message.read`

Read / delivery receipt.

```json
{
  "event": "message.read",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "messageIds": ["3EB0ABCDEF123456", "3EB0ABCDEF123457"],
    "type": "read",
    "timestamp": 1704067200
  }
}
```

---

## Connection Lifecycle Events

### `connection.connected`

WhatsApp successfully connected.

```json
{
  "event": "connection.connected",
  "data": {
    "phone": "5511999999999"
  }
}
```

---

### `connection.disconnected`

WhatsApp disconnected (logout or error).

```json
{
  "event": "connection.disconnected",
  "data": {}
}
```

---

### `connection.qr_ready`

QR Code generated for scanning.

```json
{
  "event": "connection.qr_ready",
  "data": {
    "qr": "2@abc123..."
  }
}
```

---

### `connection.pair_code`

Pairing code received (ready to display to the user).

```json
{
  "event": "connection.pair_code",
  "data": {
    "code": "ABCD-1234",
    "connected": false
  }
}
```

`connected: true` when the phone successfully paired via code.

---

### `connection.pair_status`

Pairing status update.

```json
{
  "event": "connection.pair_status",
  "data": {
    "jid": "5511999999999@s.whatsapp.net",
    "businessName": "My Business",
    "platform": "WEB",
    "status": "OK",
    "error": ""
  }
}
```

---

### `connection.logged_out`

Session logged out remotely.

```json
{
  "event": "connection.logged_out",
  "data": {
    "reason": "User logout"
  }
}
```

---

### `connection.connect_failure`

Failed to connect to WhatsApp servers.

```json
{
  "event": "connection.connect_failure",
  "data": {
    "reason": "ERROR_CONNECT",
    "message": "Connection timed out"
  }
}
```

---

### `connection.stream_error`

Stream-level error.

```json
{
  "event": "connection.stream_error",
  "data": {
    "code": "STREAM_ERR"
  }
}
```

---

### `connection.temporary_ban`

Account temporarily banned.

```json
{
  "event": "connection.temporary_ban",
  "data": {
    "code": "BAN_CODE",
    "expire": 1704153600
  }
}
```

---

### `connection.client_outdated`

Client version is no longer supported.

```json
{
  "event": "connection.client_outdated",
  "data": {}
}
```

---

### `connection.stream_replaced`

Session replaced by another one.

```json
{
  "event": "connection.stream_replaced",
  "data": {}
}
```

---

## Group Events

### `group.join`

Bot joined a group.

```json
{
  "event": "group.join",
  "data": {
    "groupId": "123456789@g.us",
    "groupName": "My Group",
    "reason": "invite",
    "type": ""
  }
}
```

---

### `group.update`

Group info changed (name, description, participants, etc.).

```json
{
  "event": "group.update",
  "data": {
    "groupId": "123456789@g.us",
    "sender": "5511999999999@s.whatsapp.net",
    "name": "New Group Name",
    "topic": "New description",
    "locked": false,
    "announce": false,
    "ephemeral": 604800,
    "delete": false,
    "link": null,
    "unlink": null,
    "newInviteLink": "https://chat.whatsapp.com/abc123"
  }
}
```

---

## Contact / Presence Events

### `contact.presence`

Contact online/offline status change.

```json
{
  "event": "contact.presence",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "status": "online",
    "lastSeen": 0
  }
}
```

`status` is `"online"` or `"offline"`.

---

### `contact.chat_presence`

Contact is typing, recording, or paused.

```json
{
  "event": "contact.chat_presence",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "state": "typing",
    "media": null
  }
}
```

`state` can be `"typing"`, `"recording"`, or `"paused"`. `media` is present when recording.

---

### `contact.picture_change`

Profile picture changed or removed.

```json
{
  "event": "contact.picture_change",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "author": "5511999999999@s.whatsapp.net",
    "action": "changed"
  }
}
```

`action` can be `"changed"` or `"removed"`.

---

### `contact.identity_change`

Contact's encryption identity changed (security notification).

```json
{
  "event": "contact.identity_change",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "implicit": false,
    "timestamp": 1704067200
  }
}
```

---

## Call Events

### `call.received`

Incoming call received (accepted or rejected).

```json
{
  "event": "call.received",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "callId": "ABC123DEF456"
  }
}
```

---

### `call.accepted`

Incoming call was accepted.

```json
{
  "event": "call.accepted",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "callId": "ABC123DEF456"
  }
}
```

---

### `call.terminated`

Call ended.

```json
{
  "event": "call.terminated",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "callId": "ABC123DEF456",
    "reason": "timeout"
  }
}
```

---

## Media Events

### `media.cleanup.completed`

Fired after each automatic TEMP_DIR cleanup cycle (runs every hour).

```json
{
  "event": "media.cleanup.completed",
  "data": {
    "filesRemoved": 12,
    "remainingBytes": 52428800
  }
}
```

`filesRemoved: 0` means nothing was old or oversized — the event still fires every cycle.

---

## AI Events

### `ai.response`

Fired when a message is received from Meta AI. Always dispatched — regardless of whether there's a pending `POST /ai/ask` request.

> **Note:** `POST /ai/ask` and `POST /ai/imagine` already return these same fields directly in the HTTP response (await with 30s timeout). Use this webhook when you need to handle responses asynchronously or when the timeout is not enough.

**Text response** (from `POST /ai/ask`):

```json
{
  "event": "ai.response",
  "data": {
    "text": "Brasília!",
    "hasImage": false,
    "imageBase64": null,
    "imageUrl": null,
    "mimeType": null,
    "messageId": "3EB0ABCDEF123456"
  }
}
```

**Image response** (from `POST /ai/imagine`):

```json
{
  "event": "ai.response",
  "data": {
    "text": "What kind of hat is the cat wearing?",
    "hasImage": true,
    "imageBase64": "/9j/4AAQSkZJRgAB...",
    "imageUrl": null,
    "mimeType": "image/jpeg",
    "messageId": "3EB0ABCDEF123456"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | `string` | Meta AI response text. For `/imagine`, this is the image caption. |
| `hasImage` | `boolean` | `true` when Meta AI sent an image. |
| `imageBase64` | `string \| null` | Base64-encoded image bytes. Set when `hasImage: true`. |
| `imageUrl` | `string \| null` | URL to the saved image (`/media/{filename}`). Only set when `META_AI_KEEP_IMAGES=true` on non-Alwaysdata environments. |
| `mimeType` | `string \| null` | Image MIME type (e.g. `"image/jpeg"`). Set when `hasImage: true`. |
| `messageId` | `string` | WhatsApp message ID of the Meta AI response. |

---

## Placeholders (Custom Body)

If the webhook has a `body` configured, these placeholders are replaced:

| Placeholder | Value |
|-------------|-------|
| `{{from}}` | Sender phone number |
| `{{text}}` | Message text |
| `{{phone}}` | Same as `{{from}}` |
| `{{id}}` | Message ID |
| `{{timestamp}}` | Current UTC timestamp |
| `{{requested}}` | (fetchMessages) requested count |
| `{{found}}` | (fetchMessages) found count |
