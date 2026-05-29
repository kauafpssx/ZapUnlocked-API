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
                "message": "Session was already clean."
            }

        removed_files = []
        for file in auth_path.iterdir():
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    shutil.rmtree(file)
                removed_files.append(file.name)
                logger.info(f"🗑️ Removed: {file.name}")
            except Exception as e:
                logger.error(f"❌ Failed to remove {file.name}: {str(e)}")

        try:
            auth_path.rmdir()
        except Exception:
            pass

        logger.info("✅ Session cleared successfully")

        return {
            "success": True,
            "message": "Session cleared. Restart the bot to generate a new QR code.",
            "removedFiles": len(removed_files)
        }
    except Exception as e:
        logger.error(f"❌ Failed to clear session: {str(e)}")
        raise e
