from pathlib import Path
from src.config.constants import DATA_DIR

async def get_volume_stats():
    data_dir = Path(DATA_DIR) / "chats"

    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "totalSize": 0,
        "fileCount": 0,
        "structure": []
    }

    def scan_dir(directory: Path):
        folder_content = []
        try:
            items = list(directory.iterdir())
        except Exception:
            return folder_content

        for item in items:
            try:
                if item.is_dir():
                    children = scan_dir(item)
                    folder_size = sum(c.get("size", 0) for c in children)
                    folder_content.append({
                        "name": item.name,
                        "type": "folder",
                        "size": folder_size,
                        "children": children
                    })
                else:
                    file_size = item.stat().st_size
                    stats["totalSize"] += file_size
                    stats["fileCount"] += 1
                    folder_content.append({
                        "name": item.name,
                        "type": "file",
                        "size": file_size
                    })
            except Exception:
                pass
        return folder_content

    stats["structure"] = scan_dir(data_dir)

    def format_size(bytes_val):
        if bytes_val == 0:
            return "0.00 MB"
        mb = bytes_val / (1024 * 1024)
        if mb < 0.01:
            return f"{(bytes_val / 1024):.2f} KB"
        return f"{mb:.2f} MB"

    return {
        "success": True,
        "totalSizeBytes": stats["totalSize"],
        "totalSizeFormatted": format_size(stats["totalSize"]),
        "fileCount": stats["fileCount"],
        "structure": stats["structure"]
    }
