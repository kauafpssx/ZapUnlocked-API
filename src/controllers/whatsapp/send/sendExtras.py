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


# ── Localização ────────────────────────────────────────
async def send_location(data: SendLocationRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

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
        return {"success": True, "message": "Localização enviada ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar localização: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Contato (único) ────────────────────────────────────
async def send_contact(data: SendContactRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

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
        return {"success": True, "message": "Contato enviado ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar contato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Vários contatos ────────────────────────────────────
async def send_contacts(data: SendContactsRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    if not data.contacts:
        raise HTTPException(status_code=400, detail="Pelo menos um contato é necessário.")

    try:
        async def process_task():
            jid = f"{data.phone}@s.whatsapp.net"
            options = await resolve_quote(jid, reply_identifier=data.reply or data.quoted_id, reply_type=data.type or "id")
            contacts_list = [{"name": c.name, "phone": c.phone} for c in data.contacts]
            await send_contacts_message(jid, contacts_list, options=options)

        await task_queue.enqueue(process_task())
        return {"success": True, "message": f"{len(data.contacts)} contato(s) enviado(s) ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar contatos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Link com preview ────────────────────────────────────
async def send_link(data: SendLinkRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    if not data.url:
        raise HTTPException(status_code=400, detail="url é obrigatório.")

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
        return {"success": True, "message": "Link enviado ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao enviar link: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Deletar mensagem ───────────────────────────────────
async def delete_msg(data: DeleteMessageRequest):
    """
    Deleta uma mensagem pelo ID.
    fromMe=True deleta do seu lado (e para todos).
    fromMe=False tenta deletar uma mensagem recebida (só do seu lado).
    """
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    if not data.messageId:
        raise HTTPException(status_code=400, detail="messageId é obrigatório.")

    try:
        jid = f"{data.phone}@s.whatsapp.net"
        target_type = data.type or "id"
        target_id = data.messageId
        
        if target_type == "text":
            found_msg = await find_message(jid, data.messageId, target_type)
            if not found_msg:
                raise HTTPException(status_code=404, detail="Mensagem não encontrada via texto.")
            target_id = found_msg["key"]["id"]
            
        await delete_message(jid, target_id, data.fromMe)
        return {"success": True, "message": "Mensagem deletada ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao deletar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Marcar como lida ───────────────────────────────────
async def read_messages(data: ReadMessagesRequest):
    """
    Marca uma lista de mensagens como lidas.
    messageIds: lista de IDs das mensagens a marcar.
    sender: JID do remetente (opcional, necessário para grupos).
    """
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    if not data.messageIds:
        raise HTTPException(status_code=400, detail="messageIds não pode ser vazio.")

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
            raise HTTPException(status_code=404, detail="Nenhuma mensagem encontrada para marcar como lida.")
            
        await mark_messages_read(jid, target_ids, data.sender)
        return {"success": True, "message": f"{len(target_ids)} mensagem(ns) marcada(s) como lida(s) ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao marcar mensagens como lidas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Editar Mensagem ───────────────────────────────────
async def send_edit(data: SendEditMessageRequest):
    """Edita uma mensagem enviada."""
    if not get_is_ready():
        raise HTTPException(status_code=503, detail="WhatsApp ainda não conectado")

    try:
        jid = f"{data.phone}@s.whatsapp.net"
        target_type = data.type or "id"
        target_id = data.messageId
        
        if target_type == "text":
            found_msg = await find_message(jid, data.messageId, target_type)
            if not found_msg:
                raise HTTPException(status_code=404, detail="Mensagem não encontrada para editar.")
            target_id = found_msg["key"]["id"]
            
        await edit_message(jid, target_id, data.message)
        return {"success": True, "message": "Mensagem editada ✅"}

    except Exception as e:
        logger.error(f"❌ Erro ao editar mensagem: {e}")
        raise HTTPException(status_code=500, detail=str(e))
