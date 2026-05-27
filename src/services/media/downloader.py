import uuid
import gc
from pathlib import Path

from src.config.constants import TEMP_DIR
from src.utils.logger import logger

MAX_SIZE = 400 * 1024 * 1024 # 400 MB

async def download_media(url: str) -> str:
    import requests
    import asyncio
    import socket
    from urllib.parse import urlparse
    import ipaddress

    logger.info(f"🌐 Iniciando download da URL: {url}")

    # --- Proteção SSRF ---
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ["http", "https"]:
            raise Exception(f"Protocolo inválido: {parsed_url.scheme}. Apenas HTTP/HTTPS são permitidos.")

        hostname = parsed_url.hostname
        if not hostname:
            raise Exception("URL inválida: hostname não identificado.")

        # Resolver IP para verificar se é privado/interno
        ip_address = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip_address)

        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast:
            logger.warning(f"🚨 Tentativa de SSRF bloqueada para IP interno: {ip_address} ({hostname})")
            raise Exception(f"Acesso negado: O endereço {hostname} resolve para um IP protegido/interno.")
            
    except Exception as ssrf_err:
        logger.error(f"❌ Falha na validação de segurança da URL: {str(ssrf_err)}")
        raise ssrf_err
    # ---------------------

    try:
        common_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/"
        }

        # Usar requests em thread para melhor compatibilidade com CDNs (bypassing TLS fingerprints do httpx)
        def perform_download():
            with requests.get(url, headers=common_headers, stream=True, timeout=60, allow_redirects=True) as r:
                r.raise_for_status()
                
                content_length = int(r.headers.get("content-length", 0))
                if content_length > MAX_SIZE:
                    size_mb = content_length / (1024 * 1024)
                    raise Exception(f"Arquivo muito grande: {size_mb:.2f}MB. O limite máximo é 400MB.")

                content_type = r.headers.get("content-type", "")
                extension = ".bin"

                if "image/" in content_type:
                    extension = "." + content_type.split("/")[1].split(";")[0]
                elif "video/" in content_type:
                    extension = "." + content_type.split("/")[1].split(";")[0]
                elif "audio/" in content_type:
                    extension = "." + content_type.split("/")[1].split(";")[0]
                elif "application/pdf" in content_type:
                    extension = ".pdf"

                if extension == ".jpeg": extension = ".jpg"
                if extension == ".mpeg": extension = ".mp3" if "audio" in content_type else ".mp4"

                filename = f"{uuid.uuid4()}{extension}"
                file_path = Path(TEMP_DIR) / filename

                logger.info(f"⏳ Gravando stream no arquivo: {filename}...")
                with open(file_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return str(file_path)

        file_path_str = await asyncio.to_thread(perform_download)
        
        file_path = Path(file_path_str)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Download concluído: {file_path.name} ({size_mb:.2f} MB)")
        gc.collect()
        return str(file_path)

    except Exception as e:
        logger.error(f"❌ Erro ao baixar mídia: {str(e)}")
        raise e
