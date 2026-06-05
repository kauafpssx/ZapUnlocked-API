"""Save UploadFile to TEMP_DIR in 1MB chunks."""

from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from src.config.constants import TEMP_DIR


async def save_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "upload").suffix or ".bin"
    tmp = Path(TEMP_DIR) / f"upload_{uuid4().hex}{suffix}"
    async with aiofiles.open(tmp, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)
    return str(tmp)
