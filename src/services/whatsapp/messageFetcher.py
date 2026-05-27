from src.utils.logger import logger
from src.services.whatsapp.client import get_sock, get_reaction_cache
from src.services.whatsapp import storage

async def fetch_messages(jid: str, limit: int = 20, msg_type: str = "all", options: dict = None):
    sock = get_sock()
    if not sock:
        raise Exception("WhatsApp não conectado")

    logger.info(f"🔍 Buscando {limit} mensagens ({msg_type}) para {jid}...")

    phone = jid.split("@")[0]
    messages = await storage.get_history(phone)

    if not messages:
        return {
            "requested": limit,
            "found": 0,
            "messages": []
        }

    reaction_map = {}
    processed_messages = []

    for m in messages:
        if not isinstance(m, dict):
            continue

        # Avoid crashing if m is missing keys
        msg_wrapper = m.get("message", {})
        msg_keys = [k for k in msg_wrapper.keys() if k not in ("messageContextInfo", "senderKeyDistributionMessage")]
        message_type = msg_keys[0] if msg_keys else "unknown"

        text = ""
        msg = msg_wrapper.get("viewOnceMessage", {}).get("message") or \
              msg_wrapper.get("viewOnceMessageV2", {}).get("message") or \
              msg_wrapper

        content = msg.get("extendedTextMessage") or msg

        if "conversation" in content:
            text = content["conversation"]
        elif isinstance(content, dict) and "extendedTextMessage" in content and "text" in content["extendedTextMessage"]:
            text = content["extendedTextMessage"]["text"]
        elif isinstance(content, dict) and "text" in content:
            text = content["text"]
        elif "imageMessage" in content:
            text = content["imageMessage"].get("caption", "[image_message]")
        elif "videoMessage" in content:
            text = content["videoMessage"].get("caption", "[video_message]")
        elif "audioMessage" in content:
            text = "[audio_message]"
        elif "stickerMessage" in content:
            text = "[sticker_message]"
        elif "documentMessage" in content:
            text = content["documentMessage"].get("caption", f"[document_message: {content['documentMessage'].get('fileName', 'arquivo')}]")
        elif "contactMessage" in content:
            text = f"[contact_message: {content['contactMessage'].get('displayName', 'desconhecido')}]"
        elif "locationMessage" in content:
            text = "[location_message]"
        elif "pollCreationMessage" in content:
            text = f"[poll_message: {content['pollCreationMessage'].get('name', '')}]"
        elif "reactionMessage" in content:
            reaction = content["reactionMessage"]
            if reaction.get("key", {}).get("id"):
                reaction_map[reaction["key"]["id"]] = reaction.get("text")
            text = f"[reaction: {reaction.get('text', 'removida')}]"
        elif "pollUpdateMessage" in content:
            text = "[poll_vote]"
        elif "protocolMessage" in content:
            text = "[protocol_message]"
        elif "interactiveMessage" in content:
            im = content["interactiveMessage"]
            text = im.get("body", {}).get("text") or im.get("header", {}).get("title") or "[interactive_message]"
        elif "buttonsResponseMessage" in content:
            text = content["buttonsResponseMessage"].get("selectedDisplayText", "[button_response]")
        elif "listResponseMessage" in content:
            text = content["listResponseMessage"].get("title", "[list_response]")
        else:
            # Fallback para outros tipos ou NativeFlow dentro de interactiveMessage
            if "interactiveMessage" in content:
                 text = "[interactive_message]"
            else:
                 text = f"[{message_type}]"

        ts_raw = m.get("messageTimestamp", 0)
        timestamp = ts_raw.get("low") if isinstance(ts_raw, dict) else ts_raw
        # Normalizar milissegundos para segundos se necessário
        if timestamp > 10000000000:
            timestamp = timestamp // 1000

        has_buttons = bool(
            msg.get("buttonsMessage") or
            msg.get("listMessage") or
            msg.get("templateMessage") or
            msg.get("buttonsResponseMessage") or
            msg.get("listResponseMessage") or
            msg.get("interactiveMessage")
        )

        processed_messages.append({
            "id": m.get("key", {}).get("id"),
            "fromMe": m.get("key", {}).get("fromMe", False),
            "pushName": m.get("pushName"),
            "text": text,
            "timestamp": timestamp,
            "mimetype": content.get("imageMessage", {}).get("mimetype") or
                        content.get("videoMessage", {}).get("mimetype") or
                        content.get("audioMessage", {}).get("mimetype") or
                        content.get("documentMessage", {}).get("mimetype"),
            "type": message_type,
            "hasButtons": has_buttons,
            "reaction": m.get("reaction"), # directly from storage if present
            "_raw": m
        })

    global_reaction_cache = get_reaction_cache()

    for pm in processed_messages:
        pm_id = pm["id"]
        if pm_id in global_reaction_cache:
            pm["reaction"] = global_reaction_cache[pm_id]
        elif pm_id in reaction_map:
            pm["reaction"] = reaction_map[pm_id]

    filtered_messages = processed_messages

    if options:
        only_reactions = options.get("onlyReactions")
        reaction_emoji = options.get("reactionEmoji")
        query = options.get("query")
        only_buttons = options.get("onlyButtons")

        if only_reactions:
            filtered_messages = [m for m in filtered_messages if m["type"] == "reactionMessage"]

        if reaction_emoji:
            filtered_messages = [m for m in filtered_messages if m["reaction"] == reaction_emoji]

        if query:
            queries = [q.strip().lower() for q in query.split(";") if q.strip()]
            filtered_messages = [
                m for m in filtered_messages
                if m["text"] and any(q in m["text"].lower() for q in queries)
            ]

        if only_buttons:
            filtered_messages = [m for m in filtered_messages if m["hasButtons"]]

    if msg_type == "sent":
        filtered_messages = [m for m in filtered_messages if m["fromMe"]]
    elif msg_type == "received":
        filtered_messages = [m for m in filtered_messages if not m["fromMe"]]

    filtered_messages.reverse()

    final_messages = []
    for m in filtered_messages[:limit]:
        m_copy = m.copy()
        if "_raw" in m_copy:
            del m_copy["_raw"]
        final_messages.append(m_copy)

    return {
        "requested": limit,
        "found": min(len(filtered_messages), limit),
        "total_found": len(filtered_messages),
        "messages": final_messages
    }

def get_recent_chats(limit: int = 20):
    from src.services.whatsapp import storage
    chats = storage.get_recent_chats_from_index()
    return chats[:limit]
