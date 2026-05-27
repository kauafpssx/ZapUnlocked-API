from fastapi import HTTPException
from src.services.whatsapp.client import get_sock
from src.controllers.whatsapp.schemas import BlockRequest


async def block_user(data: BlockRequest):
    sock = get_sock()
    if not sock:
        raise HTTPException(status_code=503, detail="WhatsApp não conectado")

    phone = data.phone
    action = data.action

    if not phone:
        raise HTTPException(status_code=400, detail="Número de telefone (phone) é obrigatório")

    if action not in ["block", "unblock"]:
        raise HTTPException(status_code=400, detail="Ação (action) deve ser 'block' ou 'unblock'")

    jid = f"{phone}@s.whatsapp.net"

    try:
        if action == "block":
            sock.block(jid)
        else:
            sock.unblock(jid)

        return {
            "success": True,
            "message": f"Usuário {phone} {'bloqueado' if action == 'block' else 'desbloqueado'} com sucesso.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
