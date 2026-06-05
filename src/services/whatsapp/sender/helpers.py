import json
import time
from google.protobuf.json_format import ParseDict

from src.services.whatsapp.client import get_client, get_is_ready
from src.services.whatsapp import storage
from src.utils.logger import logger


def build_jid(phone_or_jid: str):
    """Build a proper neonize JID from a phone number or jid string."""
    from neonize.utils.jid import build_jid as neonize_build_jid

    clean = phone_or_jid.replace(" ", "").replace("+", "")
    if "@" in clean:
        user, server = clean.split("@", 1)
        # Preserve LID server if explicitly provided
        if server == "lid":
            return neonize_build_jid(user, "lid")
        server = server.replace("@s.whatsapp.net", "").replace("@g.us", "")
        if not server or server == "s.whatsapp.net":
            server = "s.whatsapp.net"
        return neonize_build_jid(user, server)
    return neonize_build_jid(clean, "s.whatsapp.net")


def _ensure_client():
    client = get_client()
    if not client or not get_is_ready():
        raise Exception("WhatsApp is not connected.")
    return client


async def _save_to_history(jid: str, message_content: dict, res):
    """Save outgoing messages to local history."""
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


async def _dispatch_sent_event(jid: str, event_type: str, res):
    """Dispatch message.sent event to webhooks."""
    try:
        if not res or not hasattr(res, "ID"):
            return

        from src.services.webhooks.dispatcher import dispatch_event
        phone = jid.split("@")[0]

        await dispatch_event("message.sent", {
            "to": phone,
            "type": event_type,
            "messageId": res.ID
        })
    except Exception as e:
        logger.error(f"Failed to dispatch message.sent: {e}")


def _build_context_info(quoted_dict: dict):
    """Rebuild a ContextInfo proto from a history dictionary."""
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
        msg_proto = ParseDict(content_dict, Message())

        return ContextInfo(
            stanzaID=msg_id,
            participant=participant,
            quotedMessage=msg_proto
        )
    except Exception as e:
        logger.error(f"Failed to reconstruct ContextInfo for quote: {e}")
        return None


def _build_message_info(quoted_dict: dict):
    """Rebuild a Neonize Message (with Info and Payload) proto from a history dictionary."""
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
        logger.error(f"Failed to reconstruct Neonize Message for quote: {e}")
        return None
