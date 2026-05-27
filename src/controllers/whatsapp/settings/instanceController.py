import asyncio
from fastapi import HTTPException
from src.services.whatsapp.client import get_sock
from src.services.whatsapp.settingsService import get_settings, save_settings
from src.utils.logger import logger
from src.controllers.whatsapp.schemas import (
    CallRejectRequest,
    CallRejectMessageRequest,
    AutoReadRequest,
    PairPhoneRequest,
)


# ─────────────────────────────────────────────
# Ligações — Rejeitar chamadas
# ─────────────────────────────────────────────

async def set_call_reject_auto(data: CallRejectRequest):
    """
    Ativa ou desativa a rejeição automática de chamadas.
    Armazenado localmente em settings.json — o handler de eventos
    usa essa configuração para decidir se rejeita ou não as chamadas.
    """
    try:
        save_settings({"call_reject_auto": data.value})
        logger.info(f"📞 Rejeitar chamadas automático: {data.value}")
        return {"success": True, "call_reject_auto": data.value}
    except Exception as e:
        logger.error(f"Erro ao definir call_reject_auto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def set_call_reject_message(data: CallRejectMessageRequest):
    """
    Define a mensagem enviada automaticamente quando uma chamada é rejeitada.
    Armazenado localmente em settings.json.
    """
    try:
        save_settings({"call_reject_message": data.value})
        logger.info(f"📞 Mensagem de ligação rejeitada atualizada.")
        return {"success": True, "call_reject_message": data.value}
    except Exception as e:
        logger.error(f"Erro ao definir call_reject_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# Leitura automática
# ─────────────────────────────────────────────

async def set_auto_read_message(data: AutoReadRequest):
    """
    Ativa ou desativa a leitura automática de mensagens.
    Armazenado localmente em settings.json — o messageHandler
    usa essa configuração para marcar mensagens como lidas ao recebê-las.
    """
    try:
        save_settings({"auto_read_message": data.value})
        logger.info(f"✅ Leitura automática: {data.value}")
        return {"success": True, "auto_read_message": data.value}
    except Exception as e:
        logger.error(f"Erro ao definir auto_read_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# Conectar via código no telefone
# ─────────────────────────────────────────────

async def get_phone_pair_code(phone: str):
    """
    Gera um código de pareamento para conectar o número sem QR Code.
    O código pode ser inserido diretamente no WhatsApp (Dispositivos > Conectar com número).

    Requer que o cliente esteja aguardando conexão (sem sessão ativa).
    """
    sock = get_sock()
    if not sock:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp não conectado (cliente deve estar aguardando conexão)",
        )

    try:
        logger.info(f"📱 Gerando código de pareamento para: {phone}")
        # PairPhone é síncrono, requer que o cliente esteja em modo "aguardando conexão"
        # Retorna o código de 8 dígitos como string
        code = await asyncio.wait_for(
            asyncio.to_thread(sock.PairPhone, phone, True),
            timeout=15.0,
        )
        logger.info(f"✅ Código gerado para {phone}: {code}")
        return {"success": True, "phone": phone, "code": code}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Timeout ao gerar código de pareamento")
    except Exception as e:
        logger.error(f"Erro ao gerar código de pareamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
