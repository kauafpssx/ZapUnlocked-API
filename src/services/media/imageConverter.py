import asyncio
from pathlib import Path
from src.utils.logger import logger
import traceback
from src.services.media.utils import run_ffmpeg_sync

async def convert_to_webp(input_path: str, options: dict = None) -> str:
    if options is None:
        options = {}

    path = Path(input_path)
    # Ensure output differs from input (avoids FFmpeg in-place error)
    output_path = path.parent / f"{path.stem}_conv.webp"

    # v2.6 (Subprocess Threading)
    logger.info(f"🖼️ Starting sticker conversion v2.6: {path.name}")

    rmode = str(options.get("resizeMode", "pad") or "pad")
    pcolor = str(options.get("padColor", "black") or "black")
    bsigma = int(options.get("blurIntensity", 20) or 20)

    vf = ""
    if rmode == "stretch":
        vf = "scale=512:512"
    elif rmode == "cover":
        vf = "scale=512:512:force_original_aspect_ratio=increase,crop=512:512"
    elif rmode == "blur":
        vf = f"split[main][tmp];[tmp]scale=512:512:force_original_aspect_ratio=increase,crop=512:512,boxblur={bsigma}:1[bg];[main]scale=512:512:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    elif rmode in ["transparent", "contain"]:
        vf = "format=rgba,scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=#00000000"
    else: # pad
        color = "#00000000" if pcolor == "transparent" else pcolor
        format_prefix = "format=rgba," if pcolor == "transparent" or rmode == "transparent" else ""
        vf = f"{format_prefix}scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color={color}"

    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-vcodec", "libwebp",
        "-vf", vf,
        "-preset", "default",
        "-an",
        "-vsync", "0",
        "-y",
        str(output_path)
    ]
    
    # Filter empty items from command for safety
    cmd = [c for c in cmd if c]
    
    logger.debug(f"⚙️ Comando v2.6: {'|'.join(cmd)}")

    try:
        # Run synchronous subprocess without blocking the event loop (Windows-safe)
        result = await asyncio.to_thread(run_ffmpeg_sync, cmd)

        if result.returncode != 0:
            err_msg = result.stderr.decode(errors='replace').strip()
            logger.error(f"❌ FFmpeg error ({result.returncode}): {err_msg}")
            raise Exception(f"FFmpeg error: {err_msg}")

        logger.info("✅ Sticker converted!")
        return str(output_path)
    except Exception as e:
        logger.error(f"❌ Sticker conversion failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise e
