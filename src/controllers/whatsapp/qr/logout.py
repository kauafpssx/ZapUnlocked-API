from fastapi import Request, HTTPException
from src.services.whatsapp.client import logout as client_logout
from src.utils.logger import logger

async def logout(request: Request):
    try:
        keep_data = request.query_params.get("keepData") == "true"
        await client_logout(keep_data)

        message = "Disconnected successfully (data preserved)." if keep_data else "Disconnected successfully (data cleared)."

        return {"success": True, "message": message}
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": "Failed to disconnect."})
