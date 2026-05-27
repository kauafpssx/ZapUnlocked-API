import shutil
from pathlib import Path

from src.config.constants import AUTH_DIR
from src.utils.logger import logger

async def clear_session():
    try:
        auth_path = Path(AUTH_DIR)

        if not auth_path.exists():
            return {
                "success": True,
                "message": "Sessão já estava limpa"
            }

        removed_files = []
        for file in auth_path.iterdir():
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
                removed_files.append(file.name)
                logger.info(f"🗑️ Arquivo/Diretório removido: {file.name}")
            except Exception as e:
                logger.error(f"❌ Erro ao remover {file.name}: {str(e)}")

        try:
            auth_path.rmdir()
        except Exception:
            pass

        logger.info("✅ Sessão apagada com sucesso")

        return {
            "success": True,
            "message": "Sessão apagada com sucesso. Reinicie o bot para gerar novo QR Code.",
            "removedFiles": len(removed_files)
        }
    except Exception as e:
        logger.error(f"❌ Erro ao apagar sessão: {str(e)}")
        raise e
