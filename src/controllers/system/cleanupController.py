"""Controller para operações de limpeza de disco e configurações."""

from typing import Dict, Any
from fastapi import HTTPException
from src.config.constants import temp_dir, data_dir
from src.utils.logger import logger
import os
import shutil
import json


async def force_cleanup():
    """Remove todos os arquivos temporários de mídia."""
    try:
        if temp_dir.exists():
            for filename in os.listdir(temp_dir):
                filepath = temp_dir / filename
                if filepath.is_file() or filepath.is_symlink():
                    filepath.unlink()
                elif filepath.is_dir():
                    shutil.rmtree(filepath)

        return {"status": "success", "message": "Espaço em disco liberado com sucesso."}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao executar limpeza forçada: {str(e)}"
        )


async def get_cleanup_settings():
    """Retorna as configurações atuais de limpeza automática do banco."""
    try:
        db_config_file = data_dir / "db_config.json"

        settings = {"interval": 1440, "last_run": 0}

        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                data = json.load(f)
                settings.update(data)

        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao ler configs de limpeza: {str(e)}"
        )


async def update_cleanup_settings(settings: Dict[str, Any]):
    """Atualiza o intervalo de limpeza automática do banco."""
    try:
        db_config_file = data_dir / "db_config.json"

        current = {"interval": 1440, "last_run": 0}
        if db_config_file.exists():
            with open(db_config_file, "r") as f:
                current.update(json.load(f))

        if "interval" in settings:
            current["interval"] = int(settings["interval"])

        with open(db_config_file, "w") as f:
            json.dump(current, f)

        return {"status": "success", "settings": current}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar configs de limpeza: {str(e)}"
        )
