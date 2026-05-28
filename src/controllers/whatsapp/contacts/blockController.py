from fastapi import HTTPException
from neonize.utils import build_jid
from neonize.utils.enum import BlocklistAction

from src.services.whatsapp.client import get_sock
from src.controllers.whatsapp.schemas import BlockRequest


async def block_user(data: BlockRequest):
    sock = get_sock()
    if not sock:
        raise HTTPException(status_code=503, detail="WhatsApp não conectado")

    if not data.phone:
        raise HTTPException(status_code=400, detail="Número de telefone (phone) é obrigatório")

    if data.action not in ("block", "unblock"):
        raise HTTPException(status_code=400, detail="Ação (action) deve ser 'block' ou 'unblock'")

    jid = build_jid(data.phone)
    action = BlocklistAction.BLOCK if data.action == "block" else BlocklistAction.UNBLOCK

    try:
        sock.update_blocklist(jid, action)
        return {
            "success": True,
            "phone": data.phone,
            "action": data.action,
            "message": f"Usuário {data.phone} {'bloqueado' if data.action == 'block' else 'desbloqueado'} com sucesso.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
