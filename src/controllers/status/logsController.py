import gzip
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from fastapi import Query, HTTPException

from src.utils.logger import LOG_DIR

_LOG_DIR = Path(LOG_DIR)
_DATE_FMT = "%Y-%m-%d"
_TS_FMT = "%Y-%m-%d %H:%M:%S"


def _log_files() -> list[Path]:
    """Return all log files (.log and .log.gz) sorted newest first."""
    plain = list(_LOG_DIR.glob("zapunlocked_*.log"))
    compressed = list(_LOG_DIR.glob("zapunlocked_*.log.gz"))
    all_files = plain + compressed
    return sorted(all_files, key=lambda f: f.name, reverse=True)


def _file_date(f: Path) -> Optional[date]:
    name = f.name.replace("zapunlocked_", "").replace(".log.gz", "").replace(".log", "")
    try:
        return datetime.strptime(name, _DATE_FMT).date()
    except Exception:
        return None


def _parse_line_ts(line: str) -> Optional[datetime]:
    try:
        return datetime.strptime(line[:19], _TS_FMT)
    except Exception:
        return None


def _files_for_range(from_d: date, to_d: date) -> list[Path]:
    result = []
    for f in _log_files():
        d = _file_date(f)
        if d and from_d <= d <= to_d:
            result.append(f)
    return sorted(result, key=lambda f: f.name)  # oldest first


def _read_lines(files: list[Path]) -> list[str]:
    lines = []
    for f in files:
        try:
            if f.suffix == ".gz":
                with gzip.open(f, "rt", encoding="utf-8", errors="replace") as fh:
                    lines.extend(fh.read().splitlines())
            else:
                lines.extend(f.read_text(encoding="utf-8", errors="replace").splitlines())
        except Exception:
            pass
    return lines


async def list_log_files():
    files = _log_files()
    result = []
    for f in files:
        d = _file_date(f)
        if not d:
            continue
        try:
            size = f.stat().st_size
            result.append({
                "file": f.name,
                "date": str(d),
                "compressed": f.suffix == ".gz",
                "sizeBytes": size,
                "sizeFormatted": _fmt_size(size),
            })
        except Exception:
            pass
    return {"success": True, "count": len(result), "files": result}


async def get_logs(
    date: Optional[str] = Query(default=None, description="Specific date YYYY-MM-DD (default: today)"),
    from_date: Optional[str] = Query(default=None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(default=None, description="End date YYYY-MM-DD"),
    from_time: Optional[str] = Query(default=None, description="Start time HH:MM (within selected dates)"),
    to_time: Optional[str] = Query(default=None, description="End time HH:MM (within selected dates)"),
    level: Optional[str] = Query(default=None, description="Filter by level: DEBUG, INFO, WARNING, ERROR, CRITICAL"),
    search: Optional[str] = Query(default=None, description="Text search in log message"),
    limit: int = Query(default=200, ge=1, le=10000, description="Max lines returned"),
    offset: int = Query(default=0, ge=0, description="Skip first N matching lines"),
):
    # ── Resolve date range ────────────────────────────────────────────────
    today = datetime.now().date()

    if date and (from_date or to_date):
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "Use 'date' OR 'from_date'/'to_date', not both."})

    if date:
        try:
            d = datetime.strptime(date, _DATE_FMT).date()
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "Invalid 'date' format. Use YYYY-MM-DD."})
        from_d = to_d = d
    elif from_date or to_date:
        try:
            from_d = datetime.strptime(from_date, _DATE_FMT).date() if from_date else today
            to_d = datetime.strptime(to_date, _DATE_FMT).date() if to_date else today
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "Invalid date format. Use YYYY-MM-DD."})
        if from_d > to_d:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "'from_date' must be before or equal to 'to_date'."})
    else:
        from_d = to_d = today

    # ── Resolve time filter ───────────────────────────────────────────────
    from_dt = to_dt = None
    if from_time or to_time:
        try:
            if from_time:
                from_dt = datetime.strptime(from_time, "%H:%M").time()
            if to_time:
                to_dt = datetime.strptime(to_time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "Invalid time format. Use HH:MM."})

    # ── Load files ────────────────────────────────────────────────────────
    files = _files_for_range(from_d, to_d)
    if not files:
        return {
            "success": True,
            "filters": _active_filters(date, from_date, to_date, from_time, to_time, level, search),
            "total": 0,
            "returned": 0,
            "logs": [],
        }

    all_lines = _read_lines(files)

    # ── Filter ────────────────────────────────────────────────────────────
    level_upper = level.upper() if level else None
    matched = []

    for line in all_lines:
        if not line.strip():
            continue

        # Time filter
        if from_dt or to_dt:
            ts = _parse_line_ts(line)
            if ts:
                t = ts.time()
                if from_dt and t < from_dt:
                    continue
                if to_dt and t > to_dt:
                    continue

        # Level filter — format: "... | INFO     | ..."
        if level_upper:
            parts = line.split("|")
            if len(parts) < 2 or level_upper not in parts[1].upper():
                continue

        # Text search
        if search and search.lower() not in line.lower():
            continue

        matched.append(line)

    total = len(matched)
    page = matched[offset: offset + limit]

    return {
        "success": True,
        "filters": _active_filters(date, from_date, to_date, from_time, to_time, level, search),
        "total": total,
        "returned": len(page),
        "offset": offset,
        "logs": page,
    }


def _active_filters(date, from_date, to_date, from_time, to_time, level, search) -> dict:
    f = {}
    if date:
        f["date"] = date
    if from_date:
        f["from_date"] = from_date
    if to_date:
        f["to_date"] = to_date
    if from_time:
        f["from_time"] = from_time
    if to_time:
        f["to_time"] = to_time
    if level:
        f["level"] = level.upper()
    if search:
        f["search"] = search
    return f


def _fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"
