from fastapi import HTTPException
from src.services.whatsapp import storage

async def clear_storage():
    try:
        await storage.clear_all_data()
        return {
            "success": True,
            "message": "All chat files and indexes have been cleared from disk."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": str(e)}
        )
