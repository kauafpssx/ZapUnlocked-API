import json
import gc
from google.protobuf.json_format import ParseDict

# Base imports only
from src.services.whatsapp.client import get_sock, get_is_ready
from src.services.whatsapp import storage
from src.services.whatsapp import settingsService
from src.utils.logger import logger
import time

def build_jid(phone_or_jid: str):
    """Build a proper neonize JID from a phone number or jid string."""
    from neonize.utils.jid import build_jid as neonize_build_jid
    
    clean = phone_or_jid.replace(" ", "").replace("+", "")
    if "@" in clean:
        user, server = clean.split("@", 1)
        server = server.replace("@s.whatsapp.net", "").replace("@g.us", "")
        if not server or server == "s.whatsapp.net":
            server = "s.whatsapp.net"
        return neonize_build_jid(user, server)
    return neonize_build_jid(clean, "s.whatsapp.net")

def _ensure_client():
    client = get_sock()
    if not client or not get_is_ready():
        raise Exception("WhatsApp is not connected.")
    return client

async def _save_to_history(jid: str, message_content: dict, res):
    """Auxiliary function to save outgoing messages to local history."""
    try:
        if not res or not hasattr(res, "ID"):
            return
            
        phone = jid.split("@")[0]
        msg_dict = {
            "key": {
                "remoteJid": jid,
                "fromMe": True,
                "id": res.ID
            },
            "messageTimestamp": int(time.time()),
            "pushName": "You",
            "message": message_content
        }
        await storage.add_message_to_history(phone, msg_dict)
    except Exception:
        pass

def _build_context_info(quoted_dict: dict):
    """Rebuilds a ContextInfo proto from a history dictionary."""
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import ContextInfo, Message
    
    if not quoted_dict:
        return None
        
    try:
        key = quoted_dict.get("key", {})
        msg_id = key.get("id")
        remote_jid = key.get("remoteJid")
        from_me = key.get("fromMe", False)
        
        participant = quoted_dict.get("participant")
        if not participant and remote_jid:
            if not remote_jid.endswith("@g.us"):
                if not from_me:
                    participant = remote_jid

        content_dict = quoted_dict.get("message", {})
        # Special case: history might store 'conversation' as raw string sometimes 
        # but here we expect the dict format. 
        # Ensure we only pass valid fields to Message()
        msg_proto = ParseDict(content_dict, Message())
        
        return ContextInfo(
            stanzaID=msg_id,
            participant=participant,
            quotedMessage=msg_proto
        )
    except Exception as e:
        logger.error(f"❌ Failed to reconstruct ContextInfo for quote: {e}")
        return None

def _build_message_info(quoted_dict: dict):
    """Rebuilds a Neonize Message (with Info and Payload) proto from a history dictionary."""
    from neonize.proto.Neonize_pb2 import Message as NeonizeMessage, MessageInfo, MessageSource, JID as NeonizeJID
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message as WAMessage
    
    if not quoted_dict:
        return None
        
    try:
        key = quoted_dict.get("key", {})
        msg_id = key.get("id")
        remote_jid_str = key.get("remoteJid", "")
        from_me = key.get("fromMe", False)
        
        chat_jid_obj = build_jid(remote_jid_str)
        # In Neonize, JID fields are User, Server, RawAgent, Device, etc.
        source = MessageSource(
            Chat=NeonizeJID(
                User=chat_jid_obj.User, 
                Server=chat_jid_obj.Server,
                RawAgent=0,
                Device=0,
                Integrator=0
            ),
            Sender=NeonizeJID(
                User=chat_jid_obj.User, 
                Server=chat_jid_obj.Server,
                RawAgent=0,
                Device=0,
                Integrator=0
            ),
            SenderAlt=NeonizeJID(User="", Server="", RawAgent=0, Device=0, Integrator=0),
            RecipientAlt=NeonizeJID(User="", Server="", RawAgent=0, Device=0, Integrator=0),
            BroadcastListOwner=NeonizeJID(User="", Server="", RawAgent=0, Device=0, Integrator=0),
            IsFromMe=from_me,
            IsGroup=remote_jid_str.endswith("@g.us")
        )
        # Note: We fill only enough info to reconstruct the quote link
        # using defaults for required non-critical fields
        info = MessageInfo(
            ID=msg_id,
            MessageSource=source,
            ServerID=0,
            Type="",
            Pushname="",
            Timestamp=0,
            Category="",
            Multicast=False,
            MediaType="",
            Edit=""
        )
        
        content_dict = quoted_dict.get("message", {})
        msg_proto = ParseDict(content_dict, WAMessage())
        
        return NeonizeMessage(
            Info=info,
            Message=msg_proto,
            IsEphemeral=False,
            IsViewOnce=False,
            IsViewOnceV2=False,
            IsViewOnceV2Extension=False,
            IsDocumentWithCaption=False,
            IsLottieSticker=False,
            IsEdit=False,
            UnavailableRequestID="",
            RetryCount=0
        )
    except Exception as e:
        logger.error(f"❌ Failed to reconstruct Neonize Message for quote: {e}")
        return None

# ── Text ──────────────────────────────────────────────
async def send_message(jid: str, message: str, options: dict = None):
    client = _ensure_client()
    
    # Appending AI Tag if enabled
    settings = settingsService.get_settings()
    
    # EXTREME DEBUG FOR AI TAG
    from src.utils.logger import logger
    logger.info(f"🛠️ [SENDER DEBUG] ai_tag_enabled={settings.get('ai_tag_enabled')} (tipo: {type(settings.get('ai_tag_enabled'))}) | tag={settings.get('ai_tag_text')!r}")
    
    if settings.get("ai_tag_enabled"):
        tag = settings.get("ai_tag_text", " (ZapUnlocked AI)")
        if tag not in message:
            message += tag

    logger.info(f"🛠️ [SENDER DEBUG] Final text being sent to WhatsApp: {message!r}")

    ci = _build_context_info(options.get("quoted")) if options else None
    
    if ci:
        from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message as WAMessage, ExtendedTextMessage
        msg_proto = WAMessage(
            extendedTextMessage=ExtendedTextMessage(
                text=message,
                contextInfo=ci
            )
        )
        res = client.send_message(build_jid(jid), msg_proto)
    else:
        res = client.send_message(build_jid(jid), message)

    await _save_to_history(jid, {"conversation": message}, res)
    return res

# ── Buttons (NativeFlow) ─────────────────────────────
async def send_button_message(jid: str, text: str, buttons: list, options: dict = None, title: str = "", footer: str = "", image_url: str = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message, 
        MessageContextInfo, 
        InteractiveMessage, 
        DeviceListMetadata,
        FutureProofMessage
    )
    client = _ensure_client()

    interactive_msg = InteractiveMessage()
    
    # ── Header ──────────────────────────────────────────
    if image_url:
        interactive_msg.header.hasMediaAttachment = True
        try:
            # build_image_message returns a Message; .imageMessage is the ImageMessage sub-object
            img_full = client.build_image_message(image_url)
            interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load image for header: {e}")
            # Fallback: use text title in header
            interactive_msg.header.hasMediaAttachment = False
            if title:
                interactive_msg.header.title = title
    elif title:
        interactive_msg.header.title = title
        interactive_msg.header.hasMediaAttachment = False

    interactive_msg.body.text = text

    # Handle Quoting (Reply) if provided in options
    ci = _build_context_info(options.get("quoted")) if options else None
    if ci:
        interactive_msg.contextInfo.CopyFrom(ci)

    if footer:
        interactive_msg.footer.text = footer

    for i, btn_data in enumerate(buttons):
        btn = interactive_msg.nativeFlowMessage.buttons.add()
        b_type = btn_data.get("type", "quick_reply").lower()
        display_text = btn_data.get("buttonText", btn_data.get("text", f"Button {i}"))

        if b_type == "url":
            btn.name = "cta_url"
            btn.buttonParamsJSON = json.dumps({
                "display_text": display_text,
                "url": btn_data.get("url", ""),
                "merchant_url": btn_data.get("url", "")
            })
        elif b_type == "call":
            btn.name = "cta_call"
            btn.buttonParamsJSON = json.dumps({
                "display_text": display_text,
                "phoneNumber": btn_data.get("phoneNumber", btn_data.get("id", ""))
            })
        elif b_type in ["copy", "otp", "pix"]:
            btn.name = "cta_copy"
            # Prioritize 'code' then 'pixKey'. For PIX, it's usually pixKey.
            btn.buttonParamsJSON = json.dumps({
                "display_text": display_text,
                "copy_code": btn_data.get("code", btn_data.get("pixKey", ""))
            })
        elif b_type == "list":
            btn.name = "single_select"
            # Map each row: ensure 'id' field (neonize uses 'id', not 'rowID')
            raw_sections = btn_data.get("sections", [])
            mapped_sections = []
            for sec in raw_sections:
                rows = []
                for row in sec.get("rows", []):
                    rows.append({
                        "id": row.get("id", row.get("rowID", "")),
                        "title": row.get("title", ""),
                        "description": row.get("description", "")
                    })
                mapped_sections.append({"title": sec.get("title", ""), "rows": rows})
            btn.buttonParamsJSON = json.dumps({
                "title": display_text,
                "sections": mapped_sections
            })
        elif b_type == "pix":
            # Native PIX static code
            btn.name = "payment_info"
            btn.buttonParamsJSON = json.dumps({
               "payment_settings": [{ 
                  "type": "pix_static_code", 
                  "pix_static_code": { 
                     "merchant_name": btn_data.get("merchantName", btn_data.get("buttonText", "Pix")), 
                     "key": btn_data.get("pixKey", ""), 
                     "key_type": btn_data.get("pixType", btn_data.get("type_key", "EVP"))
                  } 
               }] 
            })
        elif b_type == "review_and_pay":
            # Standard WhatsApp Payment flow
            btn.name = "review_and_pay"
            payload = {
                "display_text": display_text,
                "type": "native-flow",
                "payment_configuration": btn_data.get("pixKey", ""),
                "payment_type": btn_data.get("pixType", "pix")
            }
            if btn_data.get("instructions"):
                payload["instructions"] = btn_data.get("instructions")
            btn.buttonParamsJSON = json.dumps(payload)
        else:
            # Default fallback: quick_reply
            btn.name = "quick_reply"
            btn_id = btn_data.get("buttonId", btn_data.get("id", f"btn_{i}"))
            btn.buttonParamsJSON = json.dumps({"display_text": display_text, "id": btn_id})

    # ── Final Message Assembly ──────────────────────────
    # Unified standardization for ALL devices (iOS, Android, Web)
    # NativeFlow MUST be wrapped in viewOnceMessage for many modern devices
    
    # 🎯 FIX: If NativeFlow has no header title, set one to prevent the list card from disappearing
    if not interactive_msg.header.title and not interactive_msg.header.hasMediaAttachment:
        if title:
             interactive_msg.header.title = title
        else:
             interactive_msg.header.title = "Action Required"

    interactive_msg.nativeFlowMessage.messageVersion = 1
    
    # ── Final Message Assembly ──────────────────────────
    # NativeFlow MUST be wrapped in viewOnceMessage (usually within FutureProofMessage)
    # This structure is required by neonize's specific Protobuf definitions
    msg = Message(
        viewOnceMessage=FutureProofMessage(
            message=Message(
                interactiveMessage=interactive_msg,
                messageContextInfo=MessageContextInfo(
                    deviceListMetadata=DeviceListMetadata(),
                    deviceListMetadataVersion=2
                )
            )
        )
    )

    # --- DEBUG LOGGING ---
    logger.info(f"🛠️ [SENDER DEBUG] Sending InteractiveMessage to {jid}")
    logger.info(f"🛠️ [SENDER DEBUG] Text: {text!r}")
    for i, b in enumerate(interactive_msg.nativeFlowMessage.buttons):
        logger.info(f"🛠️ [SENDER DEBUG] Button {i}: name={b.name} params={b.buttonParamsJSON}")
    # --- END DEBUG LOGGING ---

    res = client.send_message(build_jid(jid), msg)
    
    # History
    await _save_to_history(jid, {
        "interactiveMessage": {
            "body": {"text": text},
            "header": {"title": title} if title else {},
            "footer": {"text": footer} if footer else {},
            "nativeFlowMessage": {
                "buttons": [
                    {"buttonParamsJSON": b.buttonParamsJSON}
                    for b in interactive_msg.nativeFlowMessage.buttons
                ]
            }
        },
        "messageContextInfo": {
            "deviceListMetadata": {},
            "deviceListMetadataVersion": 2
        }
    }, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Polls ──────────────────────────────────────────────
async def send_poll_message(jid: str, name: str, options: list, selectable_count: int = 1, message_options: dict = None):
    from neonize.utils.enum import VoteType
    client = _ensure_client()
    
    # Cast VoteType based on selectable_count
    vote_type = VoteType.MULTIPLE if selectable_count == 0 else VoteType.SINGLE
    
    quoted_msg = message_options.get("quoted") if message_options else None
    
    msg = client.build_poll_vote_creation(
        name=name,
        options=options,
        selectable_count=vote_type,
        quoted=_build_message_info(quoted_msg)
    )
    
    # IMPORTANT: add_msg_secret=True is ESSENTIAL for polls.
    # Without it, WhatsApp does not generate the encryption key for votes (original message secret key not found).
    res = client.send_message(build_jid(jid), msg, add_msg_secret=True)
    
    await _save_to_history(jid, {
        "pollCreationMessage": {
            "name": name,
            "options": [{"optionName": opt} for opt in options]
        }
    }, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res



async def send_poll_vote_message(jid: str, poll_id: str, poll_name: str, options: list, from_me: bool = False, timestamp: int = 0):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, PollCreationMessage
    from neonize.proto.Neonize_pb2 import MessageInfo, MessageSource, JID as NeonizeJID
    from neonize.utils.jid import Jid2String
    
    client = _ensure_client()
    target_jid = build_jid(jid)
    
    # Get our own JID to accurately represent the sender
    try:
        me_jid = client.get_me().JID
    except:
        me_jid = None

    # Fully populate all JID fields in MessageInfo to satisfy Neonize's required-field validation
    def _create_full_jid(user="", server=""):
        return NeonizeJID(
            User=user,
            Server=server,
            RawAgent=0,
            Device=0,
            Integrator=0
        )
        
    def _convert_proto_jid(pjid):
        if not pjid: return _create_full_jid()
        return _create_full_jid(pjid.User, pjid.Server)

    chat_jid = _create_full_jid(target_jid.User, target_jid.Server)
    sender_jid = _convert_proto_jid(me_jid) if from_me else _create_full_jid(target_jid.User, target_jid.Server)

    msg_info = MessageInfo(
        ID=poll_id,
        ServerID=0,
        Type="poll",
        Pushname="Me" if from_me else "User",
        Timestamp=timestamp or int(time.time()),
        Category="direct",
        Multicast=False,
        MediaType="poll",
        Edit="NONE",
        MessageSource=MessageSource(
            Chat=chat_jid,
            Sender=sender_jid,
            SenderAlt=_create_full_jid(),
            RecipientAlt=_create_full_jid(),
            BroadcastListOwner=_create_full_jid(),
            IsFromMe=from_me,
            IsGroup=False
        )
    )
    
    vote_msg = client.build_poll_vote(msg_info, options)
    res = client.send_message(target_jid, vote_msg)
    
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Image ─────────────────────────────────────────────
async def send_image_message(jid: str, image_path: str, caption: str = "", as_document: bool = False, file_name: str = None, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ImageMessage, DocumentMessage
    from neonize.utils.enum import MediaType
    from pathlib import Path
    
    client = _ensure_client()
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mimetype = magic.from_buffer(image_bytes, mime=True)

    if as_document:
        # ── Send as Document ──────────────────────────
        upload = client.upload(image_bytes, MediaType.MediaDocument)
        final_name = file_name or Path(image_path).name or "imagem"
        msg = Message(
            documentMessage=DocumentMessage(
                URL=upload.url,
                directPath=upload.DirectPath,
                mediaKey=upload.MediaKey,
                fileEncSHA256=upload.FileEncSHA256,
                fileSHA256=upload.FileSHA256,
                fileLength=len(image_bytes),
                mimetype=mimetype,
                fileName=final_name,
                caption=caption,
                contextInfo=_build_context_info(options.get("quoted")) if options else None
            )
        )
        res = client.send_message(build_jid(jid), msg)
        await _save_to_history(jid, {"documentMessage": {"fileName": final_name, "caption": caption}}, res)
    else:
        # ── Send as Image ─────────────────────────────
        upload = client.upload(image_bytes, MediaType.MediaImage)
        msg = Message(
            imageMessage=ImageMessage(
                URL=upload.url,
                directPath=upload.DirectPath,
                mediaKey=upload.MediaKey,
                fileEncSHA256=upload.FileEncSHA256,
                fileSHA256=upload.FileSHA256,
                fileLength=len(image_bytes),
                mimetype=mimetype,
                caption=caption,
                contextInfo=_build_context_info(options.get("quoted")) if options else None
            )
        )
        res = client.send_message(build_jid(jid), msg)
        await _save_to_history(jid, {"imageMessage": {"caption": caption}}, res)

    del image_bytes
    gc.collect()
    return res

# ── Audio ─────────────────────────────────────────────
async def send_audio_message(jid: str, audio_path: str, is_ptt: bool = False, duration: int = 0, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, AudioMessage
    from neonize.utils.enum import MediaType
    
    client = _ensure_client()
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    if audio_path.endswith(".ogg"):
        mimetype = "audio/ogg; codecs=opus"
    elif audio_path.endswith(".m4a"):
        mimetype = "audio/mp4"
    elif audio_path.endswith(".mp3"):
        mimetype = "audio/mpeg"
    elif audio_path.endswith(".wav"):
        mimetype = "audio/wav"
    else:
        mimetype = magic.from_buffer(audio_bytes, mime=True)
    upload = client.upload(audio_bytes, MediaType.MediaAudio)

    msg = Message(
        audioMessage=AudioMessage(
            URL=upload.url,
            directPath=upload.DirectPath,
            mediaKey=upload.MediaKey,
            fileEncSHA256=upload.FileEncSHA256,
            fileSHA256=upload.FileSHA256,
            fileLength=len(audio_bytes),
            mimetype=mimetype,
            PTT=is_ptt,
            seconds=duration,
            contextInfo=_build_context_info(options.get("quoted")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"audioMessage": {}}, res)
    del audio_bytes
    gc.collect()  # kept: frees audio_bytes memory
    return res

# ── Video ─────────────────────────────────────────────
async def send_video_message(jid: str, video_path: str, caption: str = "", as_document: bool = False, gif_playback: bool = False, ptv: bool = False, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, VideoMessage
    from neonize.utils.enum import MediaType
    
    client = _ensure_client()
    if as_document:
        import os
        return await send_document_message(jid, video_path, os.path.basename(video_path), options=options)

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    mimetype = magic.from_buffer(video_bytes, mime=True)
    upload = client.upload(video_bytes, MediaType.MediaVideo)

    video_msg = VideoMessage(
        URL=upload.url,
        directPath=upload.DirectPath,
        mediaKey=upload.MediaKey,
        fileEncSHA256=upload.FileEncSHA256,
        fileSHA256=upload.FileSHA256,
        fileLength=len(video_bytes),
        mimetype=mimetype,
        caption=caption,
        gifPlayback=gif_playback,
        contextInfo=_build_context_info(options.get("quoted")) if options else None
    )

    if ptv:
        msg = Message(ptvMessage=video_msg)
    else:
        msg = Message(videoMessage=video_msg)

    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"videoMessage": {"caption": caption}}, res)
    del video_bytes
    gc.collect()  # kept: frees video_bytes memory
    return res

# ── Document ──────────────────────────────────────────
async def send_document_message(jid: str, file_path: str, file_name: str, mimetype: str = None, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, DocumentMessage
    from neonize.utils.enum import MediaType
    
    client = _ensure_client()
    with open(file_path, "rb") as f:
        doc_bytes = f.read()

    if not mimetype:
        mimetype = magic.from_buffer(doc_bytes, mime=True)
    upload = client.upload(doc_bytes, MediaType.MediaDocument)

    msg = Message(
        documentMessage=DocumentMessage(
            URL=upload.url,
            directPath=upload.DirectPath,
            mediaKey=upload.MediaKey,
            fileEncSHA256=upload.FileEncSHA256,
            fileSHA256=upload.FileSHA256,
            fileLength=len(doc_bytes),
            mimetype=mimetype,
            fileName=file_name,
            contextInfo=_build_context_info(options.get("quoted")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"documentMessage": {"title": file_name}}, res)
    del doc_bytes
    gc.collect()  # kept: frees doc_bytes memory
    return res

# ── Sticker ───────────────────────────────────────────
async def send_sticker_message(jid: str, sticker_path: str, pack: str = "", author: str = "", options: dict = None):
    client = _ensure_client()
    
    # Use the native neonize method that handles EXIF metadata and upload correctly
    # passthrough=False ensures neonize adds EXIF metadata
    res = client.send_sticker(
        to=build_jid(jid),
        file=sticker_path,
        name=pack,         # neonize maps 'name' to sticker-pack-name in EXIF
        packname=author,   # neonize maps 'packname' to sticker-pack-publisher in EXIF
        passthrough=False, # Must be False for neonize to process EXIF
        quoted=_build_message_info(options.get("quoted")) if options else None
    )
    
    await _save_to_history(jid, {"stickerMessage": {}}, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Find Message ─────────────────────────────────────
async def find_message(jid: str, identifier: str, search_type: str = "id"):
    phone = jid.split("@")[0]
    msgs = await storage.get_history(phone)

    if not msgs:
        return None

    if search_type == "text":
        norm_id = identifier.strip().lower()
        for m in reversed(msgs):
            content = m.get("message", {})
            text = ""
            if "conversation" in content:
                text = content["conversation"]
            elif "extendedTextMessage" in content:
                text = content["extendedTextMessage"].get("text", "")
            elif "imageMessage" in content:
                text = content["imageMessage"].get("caption", "")
            elif "pollCreationMessage" in content:
                text = content["pollCreationMessage"].get("name", "")
            elif "interactiveMessage" in content:
                text = content["interactiveMessage"].get("body", {}).get("text", "")
                # Check buttons
                buttons = content["interactiveMessage"].get("nativeFlowMessage", {}).get("buttons", [])
                for b in buttons:
                    try:
                        btn_params = json.loads(b.get("buttonParamsJSON", "{}"))
                        if btn_params.get("display_text", "").strip().lower() == norm_id:
                            return m
                    except:
                        continue

            if text.strip().lower() == norm_id:
                return m
        return None
    else:
        for m in msgs:
            if m.get("key", {}).get("id") == identifier:
                return m
        return None

# ── Reaction ──────────────────────────────────────────
async def send_reaction(jid: str, identifier: str, emoji: str, search_type: str = "id"):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ReactionMessage
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.utils.jid import Jid2String
    import time

    client = _ensure_client()
    found = await find_message(jid, identifier, search_type)

    target_id = identifier
    from_me = False

    if found:
        target_id = found.get("key", {}).get("id")
        from_me = found.get("key", {}).get("fromMe", False)
    elif search_type == "text":
        raise Exception(f"No recent message found with text: '{identifier}'")

    target_jid = build_jid(jid)
    jid_str = Jid2String(target_jid)

    msg = Message(
        reactionMessage=ReactionMessage(
            key=MessageKey(
                remoteJID=jid_str,
                fromMe=from_me,
                ID=target_id,
            ),
            text=emoji,
            senderTimestampMS=int(time.time() * 1000),
        )
    )
    res = client.send_message(target_jid, msg)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Location ───────────────────────────────────────────
async def send_location_message(jid: str, latitude: float, longitude: float, name: str = "", address: str = "", options: dict = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, LocationMessage

    client = _ensure_client()
    msg = Message(
        locationMessage=LocationMessage(
            degreesLatitude=latitude,
            degreesLongitude=longitude,
            name=name,
            address=address,
            contextInfo=_build_context_info(options.get("quoted")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"locationMessage": {"lat": latitude, "lng": longitude, "name": name}}, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Contact ────────────────────────────────────────────
async def send_contact_message(jid: str, contact_name: str, contact_phone: str, options: dict = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ContactMessage

    client = _ensure_client()
    phone_clean = contact_phone.lstrip("+").replace(" ", "").replace("-", "")
    vcard = (
        f"BEGIN:VCARD\nVERSION:3.0\n"
        f"N:;{contact_name};;;\n"
        f"FN:{contact_name}\n"
        f"TEL;type=CELL;type=VOICE;waid={phone_clean}:+{phone_clean}\n"
        f"END:VCARD"
    )
    msg = Message(
        contactMessage=ContactMessage(
            displayName=contact_name,
            vcard=vcard,
            contextInfo=_build_context_info(options.get("quoted")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"contactMessage": {"displayName": contact_name}}, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Multiple Contacts ──────────────────────────────────
async def send_contacts_message(jid: str, contacts: list, options: dict = None):
    """contacts: list of dicts with 'name' and 'phone' keys"""
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ContactsArrayMessage, ContactMessage

    client = _ensure_client()
    contact_msgs = []
    for c in contacts:
        name = c.get("name", "Contact")
        phone = c.get("phone", "").lstrip("+").replace(" ", "").replace("-", "")
        vcard = (
            f"BEGIN:VCARD\nVERSION:3.0\n"
            f"N:;{name};;;\n"
            f"FN:{name}\n"
            f"TEL;type=CELL;type=VOICE;waid={phone}:+{phone}\n"
            f"END:VCARD"
        )
        contact_msgs.append(ContactMessage(displayName=name, vcard=vcard))
    
    msg = Message(
        contactsArrayMessage=ContactsArrayMessage(
            displayName=f"{len(contacts)} contacts",
            contacts=contact_msgs,
            contextInfo=_build_context_info(options.get("quoted")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"contactsArrayMessage": {"count": len(contacts)}}, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Delete Message ─────────────────────────────────────
async def delete_message(jid: str, message_id: str, is_from_me: bool = True):
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.utils.jid import Jid2String

    client = _ensure_client()
    target_jid = build_jid(jid)
    sender_jid = build_jid(jid) # Default to same if fromMe (Direct Message)
    
    # Neonize revoke expects: (chat: JID, sender: JID, message_id: str)
    res = client.revoke_message(target_jid, sender_jid, message_id)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Mark as Read ───────────────────────────────────────
async def mark_messages_read(jid: str, message_ids: list, sender: str = None):
    import time
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.utils.jid import Jid2String

    client = _ensure_client()
    target_jid = build_jid(jid)
    sender_jid = build_jid(sender) if sender else target_jid
    jid_str = Jid2String(target_jid)

    keys = [
        MessageKey(remoteJID=jid_str, fromMe=False, ID=mid)
        for mid in message_ids
    ]
    res = client.mark_read(keys, int(time.time()), target_jid, sender_jid)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res

# ── Link with Preview ──────────────────────────────────
async def send_link_message(jid: str, url: str, text: str = "", title: str = "", description: str = "", thumbnail_url: str = None, options: dict = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ExtendedTextMessage
    import httpx, re

    client = _ensure_client()

    # Auto-fetch OG metadata when title/description not provided
    if not title and not description:
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers={"User-Agent": "WhatsApp/2.23.20.0"}) as http:
                r = await http.get(url)
            html = r.text
            if not title:
                m = re.search(r'<meta[^>]+(?:property=["\']og:title["\']|name=["\']og:title["\'])[^>]+content=["\']([^"\']+)["\']', html, re.I)
                if not m:
                    m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
                title = m.group(1).strip() if m else url
            if not description:
                m = re.search(r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])[^>]+content=["\']([^"\']+)["\']', html, re.I)
                description = m.group(1).strip() if m else ""
            if not thumbnail_url:
                m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                thumbnail_url = m.group(1).strip() if m else None
        except Exception as e:
            logger.debug(f"send_link: OG fetch failed ({e})")

    # text must contain the URL for WhatsApp to render the preview card
    if text:
        display_text = f"{text}\n{url}"
    else:
        display_text = url

    is_youtube = "youtube" in url.lower() or "youtu.be" in url.lower()
    ext = ExtendedTextMessage(
        text=display_text,
        matchedText=url,
        title=title or url,
        description=description,
        previewType=ExtendedTextMessage.PreviewType.VIDEO if is_youtube else ExtendedTextMessage.PreviewType.NONE,
        contextInfo=_build_context_info(options.get("quoted")) if options else None
    )

    if thumbnail_url:
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                r = await http.get(thumbnail_url)
            ext.JPEGThumbnail = r.content
        except Exception as e:
            logger.warning(f"⚠️ Failed to download link thumbnail: {e}")

    msg = Message(extendedTextMessage=ext)
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"extendedTextMessage": {"text": display_text, "canonicalUrl": url}}, res)
    return res

# ── Edit Message ───────────────────────────────────────
async def edit_message(jid: str, message_id: str, new_text: str, is_from_me: bool = True):
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ExtendedTextMessage
    from neonize.utils.jid import Jid2String

    client = _ensure_client()
    target_jid = build_jid(jid)
    
    # Build the new message that replaces the original
    new_msg = Message(conversation=new_text)
    
    # Neonize edit expects: (chat: JID, message_id: str, new_message_obj: Message)
    res = client.edit_message(target_jid, message_id, new_msg)
    # Update in local history if possible
    await _save_to_history(jid, {"conversation": new_text}, res)
    # gc.collect() — removed: Python's automatic GC is sufficient
    return res
