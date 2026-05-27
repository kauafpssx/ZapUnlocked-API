from fastapi import Request, HTTPException
from src.services.whatsapp.client import logout as client_logout
from src.utils.logger import logger

async def logout(request: Request):
    try:
        keep_data = request.query_params.get("keepData") == "true"
        await client_logout(keep_data)

        message = "Desconectado com sucesso (Dados preservados). A página será recarregada." if keep_data else "Desconectado com sucesso (Dados apagados). A página será recarregada."

        return {"success": True, "message": message}
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        raise HTTPException(status_code=500, detail={"success": False, "error": "Erro ao realizar logout"})
