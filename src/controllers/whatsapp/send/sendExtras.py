from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import (
    send_location_message,
    send_contact_message,
    send_contacts_message,
    delete_message,
    mark_messages_read,
    send_link_message,
    edit_message,
    find_message,
)
from src.services.mediaQueue import task_queue
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import (
    SendLocationRequest,
    SendContactRequest,
    SendContactsRequest,
    SendLinkRequest,
    DeleteMessageRequest,
    ReadMessagesRequest,
    SendEditMessageRequest,
)


# ── Location ────────────────────────────────────────
async def send_location(data: SendLocationRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
            await send_location_message(
                jid,
                latitude=data.lat,
                longitude=data.lng,
                name=data.name or "",
                address=data.address or "",
                options=options,
            )

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Location sent."}

    except Exception as e:
        logger.error(f"❌ Failed to send location: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Single contact ────────────────────────────────────
async def send_contact(data: SendContactRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
            await send_contact_message(
                jid,
                contact_name=data.name,
                contact_phone=data.contactPhone,
                options=options,
            )

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Contact sent."}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar contato: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Multiple contacts ────────────────────────────────────
async def send_contacts(data: SendContactsRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.contacts:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "At least one contact is required."})

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
            contacts_list = [{"name": c.name, "phone": c.phone} for c in data.contacts]
            await send_contacts_message(jid, contacts_list, options=options)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": f"{len(data.contacts)} contact(s) sent."}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar contatos: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Link com preview ────────────────────────────────────
async def send_link(data: SendLinkRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.url:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'url' is required."})

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
            await send_link_message(
                jid,
                url=data.url,
                text=data.text or "",
                title=data.title or "",
                description=data.description or "",
                thumbnail_url=data.thumbnailUrl,
                options=options,
            )

        await task_queue.enqueue(process_task())
        return {"success": True, "message": "Link sent."}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar link: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Delete message ───────────────────────────────────
async def delete_msg(data: DeleteMessageRequest):
    """
    Delete a message by ID.
    fromMe=True deletes for everyone.
    fromMe=False deletes only on your side.
    """
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.messageId:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'messageId' is required."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"
        target_type = data.type or "id"
        target_id = data.messageId
        
        if target_type == "text":
            found_msg = await find_message(jid, data.messageId, target_type)
            if not found_msg:
                raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Message not found by text."})
            target_id = found_msg["key"]["id"]

        await delete_message(jid, target_id, data.fromMe)
        return {"success": True, "message": "Message deleted."}

    except Exception as e:
        logger.error(f"❌ Failed to delete message: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Mark as read ───────────────────────────────────
async def read_messages(data: ReadMessagesRequest):
    """
    Mark a list of messages as read.
    messageIds: list of message IDs to mark.
    sender: sender JID (optional, required for groups).
    """
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    if not data.messageIds:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'messageIds' cannot be empty."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"
        target_type = data.type or "id"
        
        target_ids = []
        for msg_identifier in data.messageIds:
            if target_type == "text":
                found_msg = await find_message(jid, msg_identifier, target_type)
                if found_msg:
                    target_ids.append(found_msg["key"]["id"])
            else:
                target_ids.append(msg_identifier)
                
        if not target_ids:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "No messages found to mark as read."})

        await mark_messages_read(jid, target_ids, data.sender)
        return {"success": True, "message": f"{len(target_ids)} message(s) marked as read."}

    except Exception as e:
        logger.error(f"❌ Erro ao marcar mensagens como lidas: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})


# ── Editar Mensagem ───────────────────────────────────
async def send_edit(data: SendEditMessageRequest):
    """Edita uma mensagem enviada."""
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"
        target_type = data.type or "id"
        target_id = data.messageId
        
        if target_type == "text":
            found_msg = await find_message(jid, data.messageId, target_type)
            if not found_msg:
                raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "Message not found to edit."})
            target_id = found_msg["key"]["id"]

        await edit_message(jid, target_id, data.message)
        return {"success": True, "message": "Message edited."}

    except Exception as e:
        logger.error(f"❌ Erro ao editar mensagem: {e}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
