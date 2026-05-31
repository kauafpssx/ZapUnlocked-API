# Neonize — Knowledge Base

> Everything we learned about the `neonize` library during ZapUnlocked-API development.
> Update whenever you discover new patterns, bugs, or unexpected behavior.

---

## Table of Contents

1. [Overview](#overview)
2. [Client Structure](#client-structure)
3. [Available Methods](#available-methods)
4. [Contacts (ContactStore)](#contacts-contactstore)
5. [Sending Messages](#sending-messages)
6. [Interactive Messages (Buttons)](#interactive-messages-buttons)
7. [Polls](#polls)
8. [Variadic Functions — Pitfalls](#variadic-functions--pitfalls)
9. [Missing or Broken Methods](#missing-or-broken-methods)
10. [Async Execution](#async-execution)
11. [Protobuf Responses — Correct Fields](#protobuf-responses--correct-fields)

---

## Overview

- **Repo:** https://github.com/krypton-byte/neonize
- **Based on:** Whatsmeow (Go) with Python bindings via gRPC
- **Installation:** `pip install neonize`
- **Authentication:** Local SQLite (e.g., `auth_info/myapp.db`)

```python
from neonize.client import NewClient

client = NewClient("auth_info/session.db")
client.connect()
```

---

## Client Structure

The main client is `NewClient`. It has a sub-object `contact` of type `ContactStore`:

```python
sock = NewClient("session.db")
sock.contact  # -> ContactStore instance
```

**Important properties and sub-objects:**
| Attribute | Type | Description |
|---|---|---|
| `sock.contact` | `ContactStore` | Access to local contact database |

---

## Available Methods

### NewClient (main)

| Method | Description | Notes |
|---|---|---|
| `is_on_whatsapp(*phones)` | Checks if numbers are on WA | **VARIADIC** — see pitfalls section |
| `get_user_info(*jids)` | Returns user info (status, VerifiedName) | **VARIADIC**, returns list |
| `get_profile_picture(jid)` | Profile picture URL | May throw if not found |
| `send_message(jid, message)` | Sends generic protobuf message | Accepts any `Message` |
| `send_image(jid, image, caption)` | Shortcut to send image | Accepts URL, bytes, or path |
| `send_audio(jid, audio)` | Shortcut to send audio | |
| `send_video(jid, video, caption)` | Shortcut to send video | |
| `send_sticker(jid, sticker)` | Shortcut to send sticker (WebP) | |
| `send_document(jid, document, ...)` | Shortcut to send document | |
| `build_poll_vote_creation(name, options, selectable_count)` | Creates poll | Returns `Message` |
| `build_poll_vote(msg_info, options)` | Creates a vote on a poll | Requires correct `MessageInfo` |
| `build_image_message(url_or_bytes)` | Processes image and returns `Message` | `.imageMessage` contains the sub-object |
| `upload(bytes, MediaType)` | Uploads media | Returns `UploadResponse` |
| `revoke_message(jid, msg_key)` | Deletes message | |
| `mark_read(ids, timestamp, jid, sender)` | Marks as read | |

### ContactStore (accessed via `sock.contact`)

| Method | Description |
|---|---|
| `get_all_contacts()` | Lists all contacts from local database |
| `get_contact(jid)` | Gets contact data by JID |
| `put_pushname(jid, name)` | Saves push name to local database |
| `put_contact_name(jid, fullname, firstname)` | Saves full name to local database |
| `put_all_contact_name(entries)` | Bulk update of names |

---

## Contacts (ContactStore)

### How to get contact info

```python
from neonize.utils.jid import build_jid

jid = build_jid("5511999999999@s.whatsapp.net")
contact = sock.contact.get_contact(jid)

print(contact.FullName)      # Full name (from local db)
print(contact.FirstName)     # First name
print(contact.PushName)      # Current WhatsApp push name
print(contact.BusinessName)  # Business account name
```

> ⚠️ **Names will only be populated if the contact has interacted with the connected number or if the name was manually saved via `put_contact_name`.**

### List all contacts

```python
contacts = sock.contact.get_all_contacts()
for c in contacts:
    print(c.ContactID.User, c.PushName)
```

---

## Sending Messages

### Plain Text
```python
from neonize.utils.jid import build_jid

jid = build_jid("554499999999@s.whatsapp.net")
sock.send_message(jid, "Hello World!")
```

### Reply to Message (Quote)
```python
sock.send_message(jid, "Reply!", quoted=message_event)
```

### Image
```python
sock.send_image(jid, "https://example.com/img.jpg", caption="Caption")
sock.send_image(jid, open("file.jpg","rb").read(), caption="Local")
```

### Sticker (WebP)
```python
sock.send_sticker(jid, "https://example.com/sticker.webp")
```

### Video
```python
sock.send_video(jid, "https://example.com/video.mp4", caption="Caption")
```

---

## Interactive Messages (Buttons)

> ⚠️ **Structure confirmed by neonize-master `.pyi` files.**

### Correct structure (rootContextV1 — compatible with iOS/Android/Web)

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message, MessageContextInfo, InteractiveMessage, DeviceListMetadata
)

interactive_msg = InteractiveMessage()
interactive_msg.body.text = "Main text"
interactive_msg.footer.text = "Footer"
interactive_msg.header.title = "Title"          # text in header
# OR:
# interactive_msg.header.hasMediaAttachment = True
# interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)

btn = interactive_msg.nativeFlowMessage.buttons.add()
btn.name = "cta_url"   # or cta_call, cta_copy, quick_reply, single_select, payment_info
btn.buttonParamsJSON = json.dumps({...})

interactive_msg.nativeFlowMessage.messageVersion = 1

msg = Message(
    interactiveMessage=interactive_msg,
    messageContextInfo=MessageContextInfo(
        deviceListMetadata=DeviceListMetadata(),
        deviceListMetadataVersion=2
    )
)
sock.send_message(jid, msg)
```

### Button types and their `buttonParamsJSON`

| `btn.name` | Type | `buttonParamsJSON` |
|---|---|---|
| `cta_url` | External link | `{"display_text": "...", "url": "https://...", "merchant_url": "https://..."}` |
| `cta_call` | Call | `{"display_text": "...", "phoneNumber": "+55..."}` |
| `cta_copy` | Copy code (OTP) | `{"display_text": "...", "copy_code": "123456"}` |
| `quick_reply` | Quick reply button | `{"display_text": "...", "id": "btn_id"}` |
| `single_select` | Selection list | see below |
| `payment_info` | PIX (Business only) | `{"payment_settings": [{"type": "pix_static_code", "pix_static_code": {"merchant_name": "...", "key": "...", "key_type": "EMAIL"}}]}` |

### `single_select` — correct section format

```python
# ⚠️ IMPORTANT: use "id" (not "rowID") in rows!
btn.name = "single_select"
btn.buttonParamsJSON = json.dumps({
    "title": "View options",
    "sections": [
        {
            "title": "Section 1",
            "rows": [
                {"id": "row_1", "title": "Option 1", "description": "Description"},
                {"id": "row_2", "title": "Option 2", "description": "Another desc"}
            ]
        }
    ]
})
```

### Image in Header

```python
# build_image_message returns a full Message
# .imageMessage is the ImageMessage sub-object that goes in the header
img_full = client.build_image_message(image_url_or_bytes)
interactive_msg.header.hasMediaAttachment = True
interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)
```

### Reply/Quote inside InteractiveMessage

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import ContextInfo

ctx = ContextInfo()
ctx.stanzaId = quoted_message.Info.ID
ctx.participant = quoted_message.Info.MessageSource.Sender.User + "@s.whatsapp.net"
ctx.quotedMessage.CopyFrom(quoted_message.Message)

# contextInfo goes INSIDE InteractiveMessage, not at root
interactive_msg.contextInfo.CopyFrom(ctx)
```

---

## Polls

### Create poll

```python
from neonize.utils.enum import VoteType

vote_type = VoteType.SINGLE  # or VoteType.MULTIPLE (selectable_count=0)
msg = client.build_poll_vote_creation(
    name="Which color?",
    options=["Red", "Blue", "Green"],
    selectable_count=vote_type
)
client.send_message(jid, msg)
```

### Vote on poll

> ⚠️ **MessageSource DOES NOT HAVE `remoteJID`/`fromMe`/`ID`!**
> The correct fields are `Chat` (JID object), `IsFromMe` (bool), `IsGroup` (bool).
> The message `ID` lives in `MessageInfo.ID`, not inside `MessageSource`.

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, PollCreationMessage
from neonize.proto.Neonize_pb2 import MessageInfo, MessageSource, JID as NeonizeJID

target_jid = build_jid(phone)

msg_info = MessageInfo(
    ID=poll_message_id,          # ID of the original poll message
    MessageSource=MessageSource(
        Chat=NeonizeJID(
            User=target_jid.User,
            Server=target_jid.Server
        ),
        IsFromMe=False,
        IsGroup=False
    ),
    Message=Message(
        pollCreationMessage=PollCreationMessage(name="Poll name")
    )
)

vote_msg = client.build_poll_vote(msg_info, ["Blue"])
client.send_message(target_jid, vote_msg)
```

---

## Variadic Functions — Pitfalls

Some neonize functions are **variadic** (accept multiple arguments), not lists:

### ❌ WRONG
```python
results = sock.is_on_whatsapp(["5511999999999", "5522888888888"])  # ERROR!
user_infos = sock.get_user_info([jid1, jid2])  # ERROR!
```

### ✅ CORRECT
```python
results = sock.is_on_whatsapp("5511999999999", "5522888888888")
user_infos = sock.get_user_info(jid1, jid2)

# For a single argument:
results = sock.is_on_whatsapp(phone)  # no list!
user_infos = sock.get_user_info(jid)
```

### `is_on_whatsapp` return field
```python
results = sock.is_on_whatsapp("5511999999999")
result = results[0]
print(result.IsIn)           # bool — whether on WhatsApp (correct field!)
print(result.JID.User)       # number
print(result.VerifiedName)   # verified name (if business)
# ⚠️ result.IsOnWhatsApp DOES NOT EXIST! The correct field is IsIn
```

---

## Missing or Broken Methods

| Method | Status | Alternative |
|---|---|---|
| `get_status_message(jid)` | ❌ Doesn't exist in current version | `get_user_info` (`Status` field) |
| `get_business_profile(jid)` | ❌ Doesn't exist in current version | No alternative yet |
| `get_contact(jid)` via `NewClient` | ❌ Not directly exposed | Use `sock.contact.get_contact(jid)` |
| PIX via `payment_info` | ⚠️ Only works on Business accounts | For personal: use `cta_copy` with the key |

---

## Async Execution

Neonize is **synchronous** internally. To use with FastAPI (async), always use `asyncio.to_thread`:

```python
import asyncio

# Execution with timeout to avoid hangs
try:
    result = await asyncio.wait_for(
        asyncio.to_thread(sock.is_on_whatsapp, phone),
        timeout=4.0
    )
except asyncio.TimeoutError:
    logger.error("Timeout calling is_on_whatsapp")
```

> ⚠️ **NEVER** call neonize methods directly in async functions without `asyncio.to_thread`! This blocks the entire event loop.

### Recommended timeouts
| Method | Timeout |
|---|---|
| `is_on_whatsapp` | 4s |
| `get_user_info` | 4s |
| `get_profile_picture` | 4s |
| `sock.contact.*` | 3s |
| `send_message` | 10s |
| `send_image/video/audio` | 30s |

---

## Protobuf Responses — Correct Fields

### JID (Neonize_pb2)
```python
# Fields: User, RawAgent, Device, Integrator, Server, IsEmpty
jid.User    # "5511999999999"
jid.Server  # "s.whatsapp.net" or "g.us"
```

### MessageInfo (Neonize_pb2)
```python
# Fields: MessageSource, ID, ServerID, Type, Pushname, Timestamp, Category, Multicast, MediaType, Edit
info.ID              # Message ID (string)
info.MessageSource   # MessageSource object
info.Pushname        # sender name
info.Timestamp       # unix timestamp
```

### MessageSource (Neonize_pb2)
> ⚠️ Does NOT have `remoteJID`, `fromMe`, or `ID` field!
```python
# Fields: Chat (JID), Sender (JID), IsFromMe (bool), IsGroup (bool), AddressingMode, SenderAlt, RecipientAlt
source.Chat.User     # chat number
source.Chat.Server   # "s.whatsapp.net" or "g.us"
source.Sender.User   # sender number
source.IsFromMe      # bool
source.IsGroup       # bool
```

### IsOnWhatsAppResponse
```python
result.IsIn          # bool
result.JID.User      # string with number
result.VerifiedName  # business account name, if any
```

### ContactInfo (returned by `contact.get_contact`)
```python
contact.Found         # bool
contact.FirstName     # str
contact.FullName      # str
contact.PushName      # str
contact.BusinessName  # str
contact.RedactedPhone # str
```

### UserInfo (returned by `get_user_info`)
```python
user_info.Status           # str (bio/status)
user_info.VerifiedName.Details.VerifiedName  # verified name
user_info.VerifiedName.Details.PublicName    # public name
```

### JID Helper
```python
from neonize.utils.jid import build_jid

# Correct format:
jid = build_jid("5511999999999@s.whatsapp.net")  # individual
jid = build_jid("120363xxxxxxx-xxxxxx@g.us")     # group

# Access parts:
jid.User   # number without domain
jid.Server # "s.whatsapp.net" or "g.us"
```
