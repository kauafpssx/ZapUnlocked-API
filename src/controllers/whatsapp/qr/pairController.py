from fastapi import HTTPException
from pydantic import BaseModel
from src.services.whatsapp.client import get_sock, get_is_ready
from src.utils.logger import logger
import re
import time
import asyncio

class PairRequest(BaseModel):
    phone: str

async def pair_device(data: PairRequest):
    try:
        if get_is_ready():
            raise HTTPException(status_code=409, detail={"error": "WhatsApp já está conectado. Faça logout antes de parear novamente."})

        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "Serviço WhatsApp não inicializado"})

        clean_phone = re.sub(r'[^0-9]', '', data.phone)
        if not clean_phone:
            raise HTTPException(status_code=400, detail={"error": "Número de telefone obrigatório (ex: 5511999999999)"})

        logger.info(f"🔗 Solicitando código de pareamento para: {clean_phone}")

        try:
            import asyncio
            from src.services.whatsapp.client import get_pair_code, reset_pair_code
            
            # Limpa código anterior se existir
            reset_pair_code()
            
            loop = asyncio.get_event_loop()
            
            def run_pair_background():
                try:
                    logger.info("⚡ Iniciando sock.PairPhone na thread pool...")
                    res = sock.PairPhone(clean_phone, True)
                    logger.info(f"🔍 sock.PairPhone finalizado. Retorno: {res}")
                except Exception as e:
                    logger.error(f"❌ Erro crítico dentro da thread do PairPhone: {e}")

            # Disparar PairPhone em segundo plano
            loop.run_in_executor(None, run_pair_background)
            
            # Polling para capturar o código do evento (timeout 30 segundos)
            logger.info("⏳ Aguardando captura do código via evento/log (timeout 30s)...")
            start_wait = time.time()
            for i in range(60):
                code = get_pair_code()
                if code:
                    elapsed = time.time() - start_wait
                    logger.info(f"✅ Código capturado com sucesso após {elapsed:.1f}s: {code}")
                    return {"success": True, "code": code}
                
                if i % 10 == 0 and i > 0:
                    logger.debug(f"🔍 Ainda aguardando... ({i*0.5}s)")
                    
                await asyncio.sleep(0.5)
            
            # Se chegamos aqui, falhou
            logger.error("❌ Falha ao capturar código de pareamento após 30 segundos.")
            raise Exception("O código de pareamento não foi capturado. Verifique se o número está formatado corretamente (ex: 5551988887777)")
            
        except Exception as e:
            logger.error(f"Erro no fluxo de pareamento: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao solicitar pairing code: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)})
