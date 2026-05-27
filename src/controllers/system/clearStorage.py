from fastapi import HTTPException
from src.services.whatsapp import storage

async def clear_storage():
    try:
        await storage.clear_all_data()
        return {
            "success": True,
            "message": "Todos os arquivos de chat e índices foram apagados do disco."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Erro ao limpar storage",
                "details": str(e)
            }
        )
