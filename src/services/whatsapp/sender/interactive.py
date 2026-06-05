import json
import time

from neonize.client import NewClient
from neonize.exc import SendMessageError
from src.services.whatsapp.sender.helpers import _ensure_client, _build_context_info, _build_message_info, _save_to_history, build_jid, _dispatch_sent_event
from src.services.whatsapp import storage
from src.utils.logger import logger


async def send_list_message(jid: str, text: str, button_text: str, sections: list, options: dict = None, title: str = "", footer: str = ""):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message, ListMessage,
        MessageContextInfo, DeviceListMetadata,
    )

    client = _ensure_client()

    list_msg = ListMessage()
    list_msg.description = text
    list_msg.buttonText = button_text or "Ver opções"
    list_msg.listType = ListMessage.SINGLE_SELECT

    if title:
        list_msg.title = title
    if footer:
        list_msg.footerText = footer

    ci = _build_context_info(options.get("quoted")) if options else None
    if ci:
        list_msg.contextInfo.CopyFrom(ci)

    for sec in sections:
        section = list_msg.sections.add()
        section.title = sec.get("title", "")
        for row in sec.get("rows", []):
            r = section.rows.add()
            r.rowID = str(row.get("id", row.get("rowID", "")))
            r.title = row.get("title", "")
            r.description = row.get("description", "")

    dlm = DeviceListMetadata()
    dlm.senderTimestamp = int(time.time())

    msg = Message(
        listMessage=list_msg,
        messageContextInfo=MessageContextInfo(
            deviceListMetadata=dlm,
            deviceListMetadataVersion=2
        )
    )

    try:
        res = client.send_message(build_jid(jid), msg)
    except SendMessageError as e:
        error_str = str(e)
        if "479" in error_str:
            logger.error(f"server returned error 479 sending list")
        raise

    logger.info(f"List message sent — ID: {res.ID}")

    await _save_to_history(jid, {
        "listMessage": {
            "title": title,
            "description": text,
            "buttonText": button_text,
            "footerText": footer,
            "sections": sections,
        }
    }, res)
    await _dispatch_sent_event(jid, "list", res)
    return res


def _schedule_reconnect_sender():
    """Schedule a bot reconnect from the sender module."""
    try:
        from src.services.whatsapp.client import start_bot
        import asyncio
        loop = asyncio.get_event_loop()
        if loop and loop.is_running():
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(_reconnect_delayed(start_bot))
            )
    except Exception:
        pass


async def _reconnect_delayed(start_bot):
    import asyncio
    await asyncio.sleep(5)
    asyncio.create_task(start_bot())


async def send_button_message(jid: str, text: str, buttons: list, options: dict = None, title: str = "", footer: str = "", image_url: str = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
        Message,
        MessageContextInfo,
        InteractiveMessage,
        DeviceListMetadata,
    )
    client = _ensure_client()

    interactive_msg = InteractiveMessage()

    if image_url:
        interactive_msg.header.hasMediaAttachment = True
        try:
            img_full = client.build_image_message(image_url)
            interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)
        except Exception as e:
            logger.warning(f"Failed to load image for header: {e}")
            interactive_msg.header.hasMediaAttachment = False
            if title:
                interactive_msg.header.title = title
    elif title:
        interactive_msg.header.title = title
        interactive_msg.header.hasMediaAttachment = False

    interactive_msg.body.text = text

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
        elif b_type in ["copy", "otp"]:
            btn.name = "cta_copy"
            btn.buttonParamsJSON = json.dumps({
                "display_text": display_text,
                "copy_code": btn_data.get("code", btn_data.get("pixKey", ""))
            })
        elif b_type == "list":
            btn.name = "single_select"
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
            btn.name = "review_and_pay"
            btn.buttonParamsJSON = json.dumps({
                "reference_id": "",
                "type": "physical-goods",
                "payment_configuration": "merchant_categorization_code",
                "currency": "BRL",
                "total_amount": {"value": int(round((btn_data.get("pixValue") or 0) * 100)), "offset": 100},
                "payment_settings": [
                    {
                        "type": "pix_static_code",
                        "pix_static_code": {
                            "merchant_name": btn_data.get("merchantName", display_text),
                            "key": btn_data.get("pixKey", ""),
                            "key_type": btn_data.get("pixType", "EVP"),
                            "city": btn_data.get("pixCity") or "Brasil",
                            "description": btn_data.get("pixDescription") or "",
                        },
                    }
                ],
            })
        elif b_type == "review_and_pay":
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
            btn.name = "quick_reply"
            btn_id = btn_data.get("buttonId", btn_data.get("id", f"btn_{i}"))
            btn.buttonParamsJSON = json.dumps({"display_text": display_text, "id": btn_id})

    if not interactive_msg.header.title and not interactive_msg.header.hasMediaAttachment:
        if title:
            interactive_msg.header.title = title
        else:
            interactive_msg.header.title = "Action Required"

    interactive_msg.nativeFlowMessage.messageVersion = 1

    msg = Message(
        interactiveMessage=interactive_msg,
        messageContextInfo=MessageContextInfo(
            deviceListMetadata=DeviceListMetadata(),
            deviceListMetadataVersion=2
        )
    )

    try:
        res = client.send_message(build_jid(jid), msg)
    except SendMessageError as e:
        error_str = str(e)
        logger.error(f"SendMessageError sending interactive: {error_str}")
        raise

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
    await _dispatch_sent_event(jid, "interactive", res)
    return res


async def send_poll_message(jid: str, name: str, options: list, selectable_count: int = 1, message_options: dict = None):
    from neonize.utils.enum import VoteType
    client = _ensure_client()

    vote_type = VoteType.MULTIPLE if selectable_count == 0 else VoteType.SINGLE

    quoted_msg = message_options.get("quoted") if message_options else None

    msg = client.build_poll_vote_creation(
        name=name,
        options=options,
        selectable_count=vote_type,
        quoted=_build_message_info(quoted_msg)
    )

    res = client.send_message(build_jid(jid), msg, add_msg_secret=True)

    await _save_to_history(jid, {
        "pollCreationMessage": {
            "name": name,
            "options": [{"optionName": opt} for opt in options]
        }
    }, res)
    await _dispatch_sent_event(jid, "poll", res)
    return res


async def send_poll_vote_message(jid: str, poll_id: str, poll_name: str, options: list, from_me: bool = False, timestamp: int = 0):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message
    from neonize.proto.Neonize_pb2 import MessageInfo, MessageSource, JID as NeonizeJID
    from neonize.utils.jid import Jid2String

    client = _ensure_client()
    target_jid = build_jid(jid)

    try:
        me_jid = client.get_me().JID
    except Exception:
        me_jid = None

    def _create_full_jid(user="", server=""):
        return NeonizeJID(
            User=user,
            Server=server,
            RawAgent=0,
            Device=0,
            Integrator=0
        )

    def _convert_proto_jid(pjid):
        if not pjid:
            return _create_full_jid()
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
    await _dispatch_sent_event(jid, "poll_vote", res)
    return res


async def find_message(jid: str, identifier: str, search_type: str = "id"):
    import json
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
                buttons = content["interactiveMessage"].get("nativeFlowMessage", {}).get("buttons", [])
                for b in buttons:
                    try:
                        btn_params = json.loads(b.get("buttonParamsJSON", "{}"))
                        if btn_params.get("display_text", "").strip().lower() == norm_id:
                            return m
                    except Exception:
                        continue

            if text.strip().lower() == norm_id:
                return m
        return None
    else:
        for m in msgs:
            if m.get("key", {}).get("id") == identifier:
                return m
        return None
