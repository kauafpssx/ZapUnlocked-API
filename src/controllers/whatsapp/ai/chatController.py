from fastapi import HTTPException
from src.utils.decorators import require_whatsapp, handle_errors
from src.schemas.ai import AiAskRequest, AiImagineRequest
from src.utils.logger import logger


@require_whatsapp
@handle_errors("ask meta ai")
async def ask_controller(data: AiAskRequest):
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'message' is required."})

    from src.services.whatsapp.ai.chat import ask_meta_ai
    logger.info(f"🤖 POST /ai/ask: {data.message!r}")
    result = await ask_meta_ai(data.message)
    return {
        "success": True,
        "messageId": result.get("messageId"),
        "text": result.get("text"),
        "hasImage": result.get("hasImage", False),
    }


@require_whatsapp
@handle_errors("imagine meta ai")
async def imagine_controller(data: AiImagineRequest):
    if not data.prompt or not data.prompt.strip():
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'prompt' is required."})

    from src.services.whatsapp.ai.chat import imagine_meta_ai
    logger.info(f"🎨 POST /ai/imagine: {data.prompt!r}")
    result = await imagine_meta_ai(data.prompt)
    return {
        "success": True,
        "messageId": result.get("messageId"),
        "text": result.get("text"),
        "hasImage": result.get("hasImage", False),
        "imageBase64": result.get("imageBase64"),
        "imageUrl": result.get("imageUrl"),
        "mimeType": result.get("mimeType"),
    }
