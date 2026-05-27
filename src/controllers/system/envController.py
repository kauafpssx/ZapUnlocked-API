"""Controller para operações de variáveis de ambiente."""

from typing import Dict, Any
from fastapi import HTTPException
from src.config.constants import BASE_DIR
from src.utils.logger import logger
import os

ENV_PATH = BASE_DIR / ".env"
SENSITIVE_KEYS = ["API_KEY", "DB_PASSWORD", "SESSIONS_KEY", "SECRET_KEY"]


async def get_env_vars():
    """Retorna variáveis de ambiente do arquivo .env, ocultando chaves sensíveis."""
    try:
        from dotenv import dotenv_values

        env_dict = dotenv_values(ENV_PATH)

        filtered_env = {
            k: ("********" if k in SENSITIVE_KEYS else v)
            for k, v in env_dict.items()
        }
        return filtered_env
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler .env: {str(e)}")


async def update_env_vars(env_data: Dict[str, str]):
    """Atualiza variáveis de ambiente no arquivo .env e na memória."""
    try:
        from dotenv import set_key

        if not ENV_PATH.exists():
            ENV_PATH.touch()

        for key, value in env_data.items():
            if key in SENSITIVE_KEYS:
                logger.warning(f"🛡️ Tentativa de alteração de chave sensível bloqueada: {key}")
                continue

            set_key(str(ENV_PATH), key, value)
            os.environ[key] = value

        return {
            "status": "success",
            "message": "Variáveis de ambiente atualizadas. Chaves sensíveis (API_KEY, etc) não podem ser alteradas por aqui.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar .env: {str(e)}")
