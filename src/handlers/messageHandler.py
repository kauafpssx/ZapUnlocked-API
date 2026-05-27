import asyncio
import json

from src.utils.messageParser import parse_message, should_ignore_message
from src.utils.callbackUtils import verify_and_decode_payload
from src.services.webhookService import trigger_webhook
from src.utils.logger import logger


async def handleMessage(client, msg):
    """
    Handler principal: detecta callbacks embutidos (cb=) e despacha eventos de webhook
    para todos os tipos de mensagem recebida.
    """
    if should_ignore_message(msg):
        return

    parsed = parse_message(msg)
    if not parsed:
        return

    phone = parsed["phone"]
    text = parsed["text"] or ""
    button_response = parsed["buttonResponse"] or ""

    # ── CALLBACK DE BOTÃO (cb=) ─────────────────────────────
    callback_part = None
    if isinstance(button_response, str) and button_response.startswith("cb="):
        callback_part = button_response[3:]
    elif "|cb=" in text:
        callback_part = text.split("|cb=")[1]

    if callback_part:
        webhook_config = verify_and_decode_payload(callback_part)
        if webhook_config:
            button_label = text or "Botão clicado"
            logger.info(f'🎯 Callback detectado: "{button_label}" de {phone}')

            if webhook_config.get("reaction"):
                try:
                    from src.services.whatsapp.sender import send_reaction
                    await send_reaction(phone, msg.Info.ID, webhook_config["reaction"])
                    logger.info(f"💖 Reagiu com {webhook_config['reaction']} para {phone}")
                except Exception as err:
                    logger.error(f"Erro ao reagir à mensagem: {str(err)}")

            if webhook_config.get("url"):
                try:
                    asyncio.create_task(trigger_webhook(webhook_config, {
                        "from": phone,
                        "text": button_label,
                    }))
                except Exception as err:
                    logger.error(f"Erro ao disparar webhook de callback: {str(err)}")
        elif isinstance(button_response, str) and button_response.startswith("cb="):
            logger.warning(f"⚠️ Callback inválido ou expirado recebido de {phone}")
        return

    # ── DISPATCH DE EVENTOS PARA WEBHOOKS ──────────────────
    asyncio.create_task(_dispatch_message_event(msg, phone, parsed))


async def _dispatch_message_event(msg, phone: str, parsed: dict):
    """Identifica tipo da mensagem e despacha evento estruturado."""
    try:
        from src.services.webhookDispatcher import dispatch_event

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

        # ── Texto ────────────────────────────────────────────
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

        # ── Imagem ────────────────────────────────────────────
        if _has(raw, "imageMessage"):
            img = raw.imageMessage
            await dispatch_event("message.image", {
                **base,
                "caption": _safe_str(img, "caption"),
                "mimetype": _safe_str(img, "mimetype"),
                "fileLength": _safe_int(img, "fileLength"),
            })
            return

        # ── Vídeo ─────────────────────────────────────────────
        if _has(raw, "videoMessage"):
            vid = raw.videoMessage
            await dispatch_event("message.video", {
                **base,
                "caption": _safe_str(vid, "caption"),
                "mimetype": _safe_str(vid, "mimetype"),
                "fileLength": _safe_int(vid, "fileLength"),
                "isPTT": bool(getattr(vid, "PTT", False)),
                "isGif": bool(getattr(vid, "gifPlayback", False)),
            })
            return

        # ── Áudio ─────────────────────────────────────────────
        if _has(raw, "audioMessage"):
            aud = raw.audioMessage
            await dispatch_event("message.audio", {
                **base,
                "mimetype": _safe_str(aud, "mimetype"),
                "fileLength": _safe_int(aud, "fileLength"),
                "isPTT": bool(getattr(aud, "PTT", False)),
                "durationSeconds": _safe_int(aud, "seconds"),
            })
            return

        # ── Documento ─────────────────────────────────────────
        if _has(raw, "documentMessage"):
            doc = raw.documentMessage
            await dispatch_event("message.document", {
                **base,
                "fileName": _safe_str(doc, "fileName"),
                "caption": _safe_str(doc, "caption"),
                "mimetype": _safe_str(doc, "mimetype"),
                "fileLength": _safe_int(doc, "fileLength"),
            })
            return

        # ── Sticker ───────────────────────────────────────────
        if _has(raw, "stickerMessage"):
            stk = raw.stickerMessage
            await dispatch_event("message.sticker", {
                **base,
                "mimetype": _safe_str(stk, "mimetype"),
                "isAnimated": bool(getattr(stk, "isAnimated", False)),
            })
            return

        # ── Contato ───────────────────────────────────────────
        if _has(raw, "contactMessage"):
            ct = raw.contactMessage
            await dispatch_event("message.contact", {
                **base,
                "displayName": _safe_str(ct, "displayName"),
                "vcard": _safe_str(ct, "vcard"),
            })
            return

        # ── Localização ───────────────────────────────────────
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

        # ── Reação ────────────────────────────────────────────
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

        # ── Enquete criada ────────────────────────────────────
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

        # ── Voto em enquete ───────────────────────────────────
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

        # ── Resposta interativa (botão / lista) ───────────────
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
                    display_text = params.get("display_text", "")
                    # single_select = lista; outros = botão
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

        # ── Tipo desconhecido ─────────────────────────────────
        await dispatch_event("message.unknown", {**base, "rawType": _detect_type(raw)})

    except Exception as e:
        logger.error(f"Erro ao despachar evento de mensagem: {e}")


# ── Helpers ─────────────────────────────────────────────────

def _has(obj, field: str) -> bool:
    try:
        val = getattr(obj, field)
        return val is not None and val != type(val)()
    except Exception:
        return False


def _safe_str(obj, field: str) -> str:
    try:
        return str(getattr(obj, field) or "")
    except Exception:
        return ""


def _safe_int(obj, field: str) -> int:
    try:
        return int(getattr(obj, field) or 0)
    except Exception:
        return 0


def _detect_type(raw) -> str:
    for field in [
        "conversation", "extendedTextMessage", "imageMessage", "videoMessage",
        "audioMessage", "documentMessage", "stickerMessage", "contactMessage",
        "locationMessage", "reactionMessage", "pollCreationMessage", "pollUpdateMessage",
        "interactiveResponseMessage", "interactiveMessage", "buttonsResponseMessage",
        "listResponseMessage", "protocolMessage", "senderKeyDistributionMessage",
    ]:
        try:
            val = getattr(raw, field)
            if val is not None and val != type(val)():
                return field
        except Exception:
            pass
    return "unknown"
