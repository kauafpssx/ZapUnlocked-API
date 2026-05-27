import asyncio
from pathlib import Path
from src.utils.logger import logger
import traceback
from src.services.media.utils import run_ffmpeg_sync

async def convert_to_mp4(input_path: str) -> str:
    path = Path(input_path)
    output_path = path.parent / f"{path.stem}_conv.mp4"

    # Log de versão v2.6 (Subprocess Threading)
    logger.info(f"🎥 Iniciando conversão v2.6: {path.name}")

    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vcodec", "libx264",
        "-acodec", "aac",
        "-pix_fmt", "yuv420p",
        "-movflags", "faststart",
        "-preset", "ultrafast",
        "-vf", "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))'",
        "-y",
        str(output_path)
    ]
    
    # Filtrar qualquer item vazio no comando por segurança
    cmd = [c for c in cmd if c]
    
    logger.debug(f"⚙️ Comando v2.6: {'|'.join(cmd)}")

    try:
        # Usar asyncio.to_thread para rodar o processo síncrono sem travar o loop
        result = await asyncio.to_thread(run_ffmpeg_sync, cmd)

        if result.returncode != 0:
            err_msg = result.stderr.decode(errors='replace').strip()
            logger.error(f"❌ Erro FFmpeg ({result.returncode}): {err_msg}")
            raise Exception(f"FFmpeg error: {err_msg}")

        logger.info("✅ Vídeo convertido!")
        return str(output_path)
    except Exception as e:
        logger.error(f"❌ Erro na conversão: {str(e)}")
        logger.error(traceback.format_exc())
        raise e
