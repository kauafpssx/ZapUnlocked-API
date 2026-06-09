"""
Message type router — identifies the type of an incoming message
and dispatches the appropriate structured webhook event.
"""

import json

from src.utils.logger import logger
from src.handlers.helpers import _has, _safe_str, _safe_int, _detect_type


async def dispatch_message_event(msg, phone: str, parsed: dict):
    """Identify message type and dispatch structured event."""
    try:
        from src.services.webhooks.dispatcher import dispatch_event

        source = msg.Info.MessageSource
        message_id = msg.Info.ID
        push_name = msg.Info.Pushname or phone
        jid = parsed["jid"]
        raw = msg.Message

        base = {
            "messageId": message_id,
            "from": phone,
            "fromName": push_name,
            "fromJid": jid,
            "isGroup": source.IsGroup,
        }

        # ── Text ────────────────────────────────────────────
        if raw.conversation or _has(raw, "extendedTextMessage"):
            text = raw.conversation or ""
            quoted = None
            try:
                ext = raw.extendedTextMessage
                if ext.text:
                    text = ext.text
                if ext.contextInfo.stanzaID:
                    quoted = {
                        "id": ext.contextInfo.stanzaID,
                        "fromMe": ext.contextInfo.remoteJid == "" or False,
                    }
            except Exception:
                pass

            await dispatch_event("message.text", {
                **base,
                "text": text,
                "quoted": quoted,
            })
            return

        # ── Image ────────────────────────────────────────────
        if _has(raw, "imageMessage"):
            img = raw.imageMessage
            mime = _safe_str(img, "mimetype")
            file_length = _safe_int(img, "fileLength")
            from src.services.whatsapp.media_receiver import try_download_media
            media = await try_download_media(msg, file_length, mime, "image")
            await dispatch_event("message.image", {
                **base,
                "caption": _safe_str(img, "caption"),
                "fileLength": file_length,
                **media,
            })
            return

        # ── Video ─────────────────────────────────────────────
        if _has(raw, "videoMessage"):
            vid = raw.videoMessage
            mime = _safe_str(vid, "mimetype")
            file_length = _safe_int(vid, "fileLength")
            from src.services.whatsapp.media_receiver import try_download_media
            media = await try_download_media(msg, file_length, mime, "video")
            await dispatch_event("message.video", {
                **base,
                "caption": _safe_str(vid, "caption"),
                "fileLength": file_length,
                "isPTT": bool(getattr(vid, "PTT", False)),
                "isGif": bool(getattr(vid, "gifPlayback", False)),
                **media,
            })
            return

        # ── Audio ─────────────────────────────────────────────
        if _has(raw, "audioMessage"):
            aud = raw.audioMessage
            mime = _safe_str(aud, "mimetype")
            file_length = _safe_int(aud, "fileLength")
            from src.services.whatsapp.media_receiver import try_download_media
            media = await try_download_media(msg, file_length, mime, "audio")
            await dispatch_event("message.audio", {
                **base,
                "fileLength": file_length,
                "isPTT": bool(getattr(aud, "PTT", False)),
                "durationSeconds": _safe_int(aud, "seconds"),
                **media,
            })
            return

        # ── Document ─────────────────────────────────────────
        if _has(raw, "documentMessage"):
            doc = raw.documentMessage
            mime = _safe_str(doc, "mimetype")
            file_length = _safe_int(doc, "fileLength")
            orig_name = _safe_str(doc, "fileName")
            from src.services.whatsapp.media_receiver import try_download_media
            media = await try_download_media(msg, file_length, mime, "document", file_name=orig_name)
            await dispatch_event("message.document", {
                **base,
                "caption": _safe_str(doc, "caption"),
                "fileLength": file_length,
                **media,
            })
            return

        # ── Sticker ───────────────────────────────────────────
        if _has(raw, "stickerMessage"):
            stk = raw.stickerMessage
            mime = _safe_str(stk, "mimetype")
            file_length = _safe_int(stk, "fileLength") if hasattr(stk, "fileLength") else 0
            from src.services.whatsapp.media_receiver import try_download_media
            media = await try_download_media(msg, file_length, mime, "sticker")
            await dispatch_event("message.sticker", {
                **base,
                "isAnimated": bool(getattr(stk, "isAnimated", False)),
                **media,
            })
            return

        # ── Contact ──────────────────────────────────────────
        if _has(raw, "contactMessage"):
            ct = raw.contactMessage
            await dispatch_event("message.contact", {
                **base,
                "displayName": _safe_str(ct, "displayName"),
                "vcard": _safe_str(ct, "vcard"),
            })
            return

        # ── Contacts array ───────────────────────────────────
        if _has(raw, "contactsArrayMessage"):
            arr = raw.contactsArrayMessage
            contacts = []
            try:
                contacts = [
                    {"displayName": _safe_str(c, "displayName"), "vcard": _safe_str(c, "vcard")}
                    for c in arr.contacts
                ]
            except Exception:
                pass
            await dispatch_event("message.contacts", {
                **base,
                "displayName": _safe_str(arr, "displayName"),
                "count": len(contacts),
                "contacts": contacts,
            })
            return

        # ── Location ───────────────────────────────────────────
        if _has(raw, "locationMessage"):
            loc = raw.locationMessage
            await dispatch_event("message.location", {
                **base,
                "lat": getattr(loc, "degreesLatitude", None),
                "lng": getattr(loc, "degreesLongitude", None),
                "name": _safe_str(loc, "name"),
                "address": _safe_str(loc, "address"),
            })
            return

        # ── Reaction ────────────────────────────────────────────
        if _has(raw, "reactionMessage"):
            react = raw.reactionMessage
            emoji = _safe_str(react, "text")
            await dispatch_event("message.reaction", {
                **base,
                "emoji": emoji,
                "targetMessageId": _safe_str(react.key, "ID") if react.key else None,
                "isRemoved": emoji == "",
            })
            return

        # ── Protocol message (Deletion) ───────────────────────
        if _has(raw, "protocolMessage"):
            pm = raw.protocolMessage
            # Type 0 is REVOKE (deletion)
            if pm.type == 0:
                await dispatch_event("message.deleted", {
                    **base,
                    "targetMessageId": _safe_str(pm.key, "ID") if pm.key else None,
                })
                return

        # ── Poll created ─────────────────────────────────────
        if _has(raw, "pollCreationMessage"):
            poll = raw.pollCreationMessage
            options = []
            try:
                options = [o.optionName for o in poll.options]
            except Exception:
                pass
            await dispatch_event("message.poll_created", {
                **base,
                "pollName": _safe_str(poll, "name"),
                "options": options,
            })
            return

        # ── Poll vote ────────────────────────────────────────
        if _has(raw, "pollUpdateMessage"):
            vote = raw.pollUpdateMessage
            selected = []
            try:
                selected = [o for o in vote.vote.selectedOptions]
            except Exception:
                pass
            poll_id = None
            try:
                poll_id = vote.pollCreationMessageKey.ID
            except Exception:
                pass
            await dispatch_event("message.poll_vote", {
                **base,
                "pollId": poll_id,
                "selectedOptions": selected,
            })
            return

        # ── Interactive response (button / list) ───────────────
        if _has(raw, "interactiveResponseMessage"):
            resp = raw.interactiveResponseMessage
            button_id = None
            display_text = ""
            resp_type = "unknown"
            try:
                native = resp.nativeFlowResponseMessage
                if native:
                    params = json.loads(native.paramsJSON)
                    button_id = params.get("id", "")
                    display_text = params.get("display_text", "") or params.get("title", "")
                    resp_type = "list_reply" if params.get("id", "").isdigit() else "button_reply"
            except Exception:
                pass
            try:
                if not button_id and resp.buttonResponseMessage:
                    button_id = resp.buttonResponseMessage.selectedButtonID
                    display_text = resp.buttonResponseMessage.selectedDisplayText or ""
                    resp_type = "button_reply"
            except Exception:
                pass

            if resp_type == "list_reply":
                await dispatch_event("message.list_reply", {
                    **base,
                    "rowId": button_id,
                    "title": display_text,
                })
            else:
                await dispatch_event("message.button_reply", {
                    **base,
                    "buttonId": button_id,
                    "displayText": display_text,
                    "type": "quick_reply",
                })
            return

        # ── Legacy: buttonsResponseMessage ────────────────────
        if _has(raw, "buttonsResponseMessage"):
            br = raw.buttonsResponseMessage
            await dispatch_event("message.button_reply", {
                **base,
                "buttonId": _safe_str(br, "selectedButtonID"),
                "displayText": _safe_str(br, "selectedDisplayText"),
                "type": "legacy_button",
            })
            return

        # ── Template button reply (Android) ──────────────────
        if _has(raw, "templateButtonReplyMessage"):
            tbr = raw.templateButtonReplyMessage
            await dispatch_event("message.button_reply", {
                **base,
                "buttonId": _safe_str(tbr, "selectedID"),
                "displayText": _safe_str(tbr, "selectedDisplayText"),
                "type": "template_button",
            })
            return

        # ── Legacy: listResponseMessage ───────────────────────
        if _has(raw, "listResponseMessage"):
            lr = raw.listResponseMessage
            await dispatch_event("message.list_reply", {
                **base,
                "rowId": _safe_str(lr, "singleSelectReply.selectedRowId") or _safe_str(lr, "title"),
                "title": _safe_str(lr, "title"),
                "description": _safe_str(lr, "description"),
            })
            return

        # ── Unknown type ─────────────────────────────────────
        raw_type = _detect_type(raw)
        try:
            field_names = [f[0].name for f in raw.ListFields()]
            logger.debug(f"Unknown message fields: {field_names}")
        except Exception:
            pass
        await dispatch_event("message.unknown", {**base, "rawType": raw_type})

    except Exception as e:
        logger.error(f"Failed to dispatch message event: {e}")
