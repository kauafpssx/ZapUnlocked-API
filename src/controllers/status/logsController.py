from pathlib import Path
from datetime import datetime
from fastapi import Query
from src.utils.logger import LOG_DIR


async def get_logs(limit: int = Query(default=100, ge=1, le=5000)):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(LOG_DIR) / f"zapunlocked_{today}.log"

    if not log_file.exists():
        return {"success": True, "date": today, "lines": limit, "logs": []}

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    tail = [line.rstrip("\n") for line in lines[-limit:]]
    return {"success": True, "date": today, "lines": len(tail), "logs": tail}
