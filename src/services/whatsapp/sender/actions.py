import time
import json
import re
import httpx

from src.services.whatsapp.sender.helpers import _ensure_client, _build_context_info, _save_to_history, build_jid, _dispatch_sent_event
from src.utils.logger import logger


async def send_reaction(jid: str, identifier: str, emoji: str, search_type: str = "id"):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ReactionMessage
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.utils.jid import Jid2String

    from src.services.whatsapp.sender.interactive import find_message

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
    await _dispatch_sent_event(jid, "reaction", res)
    return res


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
    await _dispatch_sent_event(jid, "location", res)
    return res


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
    await _dispatch_sent_event(jid, "contact", res)
    return res


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
    await _dispatch_sent_event(jid, "contacts", res)
    return res


async def send_link_message(jid: str, url: str, text: str = "", title: str = "", description: str = "", thumbnail_url: str = None, options: dict = None):
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ExtendedTextMessage

    client = _ensure_client()

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
    await _dispatch_sent_event(jid, "link", res)
    return res


async def delete_message(jid: str, message_id: str, is_from_me: bool = True):
    client = _ensure_client()
    target_jid = build_jid(jid)
    sender_jid = client.get_me().JID if is_from_me else build_jid(jid)

    res = client.revoke_message(target_jid, sender_jid, message_id)
    await _dispatch_sent_event(jid, "delete", res)
    return res


async def mark_messages_read(jid: str, message_ids: list, sender: str = None):
    from neonize.utils.enum import ReceiptType

    client = _ensure_client()
    target_jid = build_jid(jid)
    sender_jid = build_jid(sender) if sender else target_jid

    res = client.mark_read(
        *message_ids,
        chat=target_jid,
        sender=sender_jid,
        receipt=ReceiptType.READ,
    )
    return res


async def edit_message(jid: str, message_id: str, new_text: str, is_from_me: bool = True):
    from neonize.proto.waCommon.WACommon_pb2 import MessageKey
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ExtendedTextMessage
    from neonize.utils.jid import Jid2String

    client = _ensure_client()
    target_jid = build_jid(jid)

    new_msg = Message(conversation=new_text)
    res = client.edit_message(target_jid, message_id, new_msg)
    await _save_to_history(jid, {"conversation": new_text}, res)
    await _dispatch_sent_event(jid, "edit", res)
    return res
