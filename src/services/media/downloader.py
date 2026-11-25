import uuid
from pathlib import Path
from urllib.parse import urljoin, urlparse

from src.config.constants import TEMP_DIR
from src.utils.logger import logger

MAX_SIZE = 400 * 1024 * 1024  # 400 MB
MAX_REDIRECTS = 5


def _is_protected_ip(ip_address: str) -> bool:
    import ipaddress

    try:
        ip_obj = ipaddress.ip_address(ip_address)
    except ValueError:
        return True
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def _validate_url(url: str) -> None:
    import socket

    parsed_url = urlparse(url)
    if parsed_url.scheme not in ("http", "https"):
        raise Exception(f"Invalid protocol: {parsed_url.scheme}. Only HTTP/HTTPS allowed.")

    hostname = parsed_url.hostname
    if not hostname:
        raise Exception("Invalid URL: hostname not identified.")

    # Block obvious local names even if DNS resolution is mocked.
    lowered = hostname.lower()
    if lowered in {"localhost", "localhost.localdomain"} or lowered.endswith(".localhost"):
        raise Exception(f"Access denied: {hostname} resolves to a protected/internal IP.")

    try:
        ip_address = socket.gethostbyname(hostname)
    except Exception as exc:
        raise Exception(f"DNS resolution failed for {hostname}: {exc}")

    if _is_protected_ip(ip_address):
        logger.warning(f"🚨 SSRF attempt blocked for internal IP: {ip_address} ({hostname})")
        raise Exception(f"Access denied: {hostname} resolves to a protected/internal IP.")


async def download_media(url: str) -> str:
    import asyncio
    import requests

    logger.info(f"🌐 Downloading: {url}")

    current_url = url
    response = None
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _validate_url(current_url)
            candidate = requests.get(
                current_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
                    "Referer": "https://www.google.com/",
                },
                stream=True,
                timeout=60,
                allow_redirects=False,
            )
            if candidate.status_code in (301, 302, 303, 307, 308):
                location = candidate.headers.get("location")
                candidate.close()
                if not location:
                    raise Exception("Redirect without Location header.")
                current_url = urljoin(current_url, location)
                continue
            response = candidate
            break
        else:
            raise Exception("Too many redirects.")

        if response is None:
            raise Exception("Failed to obtain response.")

        response.raise_for_status()

        content_length = int(response.headers.get("content-length", 0) or 0)
        if content_length > MAX_SIZE:
            size_mb = content_length / (1024 * 1024)
            raise Exception(f"File too large: {size_mb:.2f}MB. Maximum allowed is 400MB.")

        content_type = response.headers.get("content-type", "")
        extension = ".bin"
        if "image/" in content_type:
            extension = "." + content_type.split("/")[1].split(";")[0]
        elif "video/" in content_type:
            extension = "." + content_type.split("/")[1].split(";")[0]
        elif "audio/" in content_type:
            extension = "." + content_type.split("/")[1].split(";")[0]
        elif "application/pdf" in content_type:
            extension = ".pdf"
        if extension == ".jpeg":
            extension = ".jpg"
        if extension == ".mpeg":
            extension = ".mp3" if "audio" in content_type else ".mp4"

        filename = f"{uuid.uuid4()}{extension}"
        file_path = Path(TEMP_DIR) / filename
        logger.info(f"⏳ Writing stream to file: {filename}...")

        total = 0
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    total += len(chunk)
                    if total > MAX_SIZE:
                        raise Exception("File too large: streamed content exceeded 400MB.")
                    f.write(chunk)

        size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Download complete: {file_path.name} ({size_mb:.2f} MB)")
        return str(file_path)

    except Exception as e:
        logger.error(f"❌ Media download failed: {str(e)}")
        raise e
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass