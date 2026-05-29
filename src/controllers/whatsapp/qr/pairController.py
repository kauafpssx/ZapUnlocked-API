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
            raise HTTPException(status_code=409, detail={"error": "WHATSAPP_ALREADY_CONNECTED", "message": "WhatsApp is already connected. Disconnect before pairing again."})

        sock = get_sock()
        if not sock:
            raise HTTPException(status_code=503, detail={"error": "SERVICE_UNAVAILABLE", "message": "WhatsApp service is not initialized."})

        clean_phone = re.sub(r'[^0-9]', '', data.phone)
        if not clean_phone:
            raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "Phone number is required (e.g. 5511999999999)."})

        logger.info(f"🔗 Requesting pairing code for: {clean_phone}")

        try:
            import asyncio
            from src.services.whatsapp.client import get_pair_code, reset_pair_code
            
            # Clear any previous code
            reset_pair_code()
            
            loop = asyncio.get_event_loop()
            
            def run_pair_background():
                try:
                    logger.info("⚡ Starting sock.PairPhone in thread pool...")
                    res = sock.PairPhone(clean_phone, True)
                    logger.info(f"🔍 sock.PairPhone finished. Result: {res}")
                except Exception as e:
                    logger.error(f"❌ Critical error inside PairPhone thread: {e}")

            # Fire PairPhone in the background
            loop.run_in_executor(None, run_pair_background)
            
            # Poll to capture the code from the event (30s timeout)
            logger.info("⏳ Waiting for code capture via event/log (30s timeout)...")
            start_wait = time.time()
            for i in range(60):
                code = get_pair_code()
                if code:
                    elapsed = time.time() - start_wait
                    logger.info(f"✅ Code captured after {elapsed:.1f}s: {code}")
                    return {"success": True, "code": code}
                
                if i % 10 == 0 and i > 0:
                    logger.debug(f"🔍 Still waiting... ({i*0.5}s)")
                    
                await asyncio.sleep(0.5)
            
            # Reached here means timeout — pairing failed
            logger.error("❌ Failed to capture pairing code after 30 seconds.")
            raise Exception("Pairing code was not captured. Check that the phone number is correctly formatted (e.g. 5551988887777).")

        except Exception as e:
            logger.error(f"Pairing flow error: {e}")
            raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": str(e)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to request pairing code: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
