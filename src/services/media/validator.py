"""MIME type validation for media routes. Uses python-magic to read actual file bytes."""

from fastapi import HTTPException

try:
    import magic as _magic
    def _detect(path: str) -> str:
        return _magic.from_file(path, mime=True)
except Exception:
    import mimetypes
    def _detect(path: str) -> str:
        t, _ = mimetypes.guess_type(path)
        return t or "application/octet-stream"


ALLOWED: dict[str, list[str]] = {
    "image": [
        "image/jpeg", "image/png", "image/webp",
        "image/bmp", "image/tiff", "image/avif", "image/heic",
        "image/heif", "image/x-icon",
    ],
    "audio": [
        "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav",
        "audio/webm", "audio/aac", "audio/flac", "audio/x-m4a",
        "audio/x-wav", "audio/x-flac", "audio/3gpp",
        "video/mp4",  # some m4a files are detected as video/mp4
    ],
    "video": [
        "video/mp4", "video/quicktime", "video/webm", "video/x-msvideo",
        "video/mpeg", "video/3gpp", "video/3gpp2", "video/x-matroska",
        "video/x-flv", "video/ogg",
    ],
    "gif": [
        "image/gif",
        "image/webp",  # animated WebP
    ],
    "document": [
        # PDF
        "application/pdf",
        # Word
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # Excel
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        # PowerPoint
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        # Text
        "text/plain", "text/csv", "text/html", "text/xml",
        "application/json", "application/xml",
        # Archives
        "application/zip", "application/x-zip-compressed",
        "application/x-rar-compressed", "application/x-7z-compressed",
        "application/x-tar", "application/gzip",
        # Generic binary (last resort)
        "application/octet-stream",
    ],
    "sticker": [
        "image/webp", "image/png", "image/jpeg", "image/gif",
        "image/bmp", "image/tiff",
        "video/mp4", "video/webm", "video/quicktime", "video/3gpp",
    ],
}

# Types that produce animated stickers (GIF/video → animated WebP)
ANIMATED_STICKER_TYPES = {
    "image/gif",
    "video/mp4", "video/webm", "video/quicktime",
    "video/3gpp", "video/mpeg",
}


def _normalize(mime: str) -> str:
    return mime.split(";")[0].strip().lower()


def validate_media(path: str, media_type: str) -> str:
    """
    Detects real MIME type from file bytes.
    Raises 415 if not in allowlist for `media_type`.
    Returns detected MIME type.
    """
    mime = _normalize(_detect(path))
    allowed = ALLOWED.get(media_type, [])
    if mime not in allowed:
        raise HTTPException(
            status_code=415,
            detail={
                "error": "UNSUPPORTED_MEDIA_TYPE",
                "message": f"File type '{mime}' is not allowed for {media_type}.",
                "allowed": allowed,
            },
        )
    return mime


def is_animated_sticker_source(mime: str) -> bool:
    return mime in ANIMATED_STICKER_TYPES
