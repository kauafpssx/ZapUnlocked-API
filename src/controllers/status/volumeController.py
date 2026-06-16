from pathlib import Path
from src.config.constants import DATA_DIR


async def get_volume_status():
    data_dir = Path(DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    file_count = 0

    def scan(directory: Path):
        nonlocal total_bytes, file_count
        entries = []
        try:
            items = sorted(directory.iterdir())
        except PermissionError:
            return entries
        for item in items:
            try:
                if item.is_dir():
                    children = scan(item)
                    size = sum(c["size"] for c in children)
                    entries.append({"name": item.name, "type": "folder", "size": size, "children": children})
                else:
                    size = item.stat().st_size
                    total_bytes += size
                    file_count += 1
                    entries.append({"name": item.name, "type": "file", "size": size})
            except Exception:
                pass
        return entries

    structure = scan(data_dir)

    def fmt(b):
        if b == 0:
            return "0.00 MB"
        mb = b / 1024 / 1024
        return f"{b / 1024:.2f} KB" if mb < 0.01 else f"{mb:.2f} MB"

    return {
        "success": True,
        "totalSizeBytes": total_bytes,
        "totalSizeFormatted": fmt(total_bytes),
        "fileCount": file_count,
        "structure": structure,
    }
