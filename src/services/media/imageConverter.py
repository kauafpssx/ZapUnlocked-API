import asyncio
from pathlib import Path
from src.utils.logger import logger
import traceback
from src.services.media.utils import run_ffmpeg_sync

# WhatsApp sticker limits: animated <= 500 KB and <= 10 s (static <= 100 KB).
ANIMATED_MAX_BYTES = 500 * 1000
ANIMATED_MAX_SECONDS = 10
# (libwebp quality, fps cap or None to keep source fps, internal detail px or None), best
# first. The last steps shrink then re-enlarge the picture (softer, but the canvas stays 512x512).
ANIMATED_QUALITY_LADDER = [(70, None, None), (55, 20, None), (45, 15, None), (35, 12, None),
                           (25, 10, None), (20, 10, 384), (15, 8, 320), (10, 8, 256)]

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
    
    logger.debug(f"⚙️ Command v2.6: {'|'.join(cmd)}")

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


async def convert_to_animated_webp(input_path: str, options: dict = None) -> str:
    """Convert GIF or video to animated WebP sticker (512x512, all frames preserved)."""
    if options is None:
        options = {}

    path = Path(input_path)
    output_path = path.parent / f"{path.stem}_anim.webp"

    rmode = str(options.get("resizeMode", "pad") or "pad")
    pcolor = str(options.get("padColor", "black") or "black")
    bsigma = int(options.get("blurIntensity", 20) or 20)

    if rmode == "stretch":
        vf = "scale=512:512"
    elif rmode == "cover":
        vf = "scale=512:512:force_original_aspect_ratio=increase,crop=512:512"
    elif rmode == "blur":
        vf = f"split[main][tmp];[tmp]scale=512:512:force_original_aspect_ratio=increase,crop=512:512,boxblur={bsigma}:1[bg];[main]scale=512:512:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    else:
        color = "#00000000" if pcolor in ("transparent", None) else pcolor
        fmt = "format=rgba," if pcolor == "transparent" else ""
        vf = f"{fmt}scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color={color}"

    # WhatsApp rejects animated stickers > 500 KB or > 10 s when they are saved/forwarded,
    # even though the send itself succeeds. Try the best quality first and step down
    # (quality, fps) until the file fits, keeping the 512x512 canvas.
    logger.info(f"🎞️ Converting animated sticker: {path.name}")
    try:
        for quality, fps, detail in ANIMATED_QUALITY_LADDER:
            chain = f"fps={fps},{vf}" if fps else vf
            if detail:
                chain += f",scale={detail}:{detail}:flags=bilinear,scale=512:512:flags=bicubic"
            cmd = [
                "ffmpeg",
                "-i", str(input_path),
                "-t", str(ANIMATED_MAX_SECONDS),
                "-vcodec", "libwebp",
                "-vf", chain,
                "-quality", str(quality),
                "-compression_level", "6",
                "-preset", "default",
                "-loop", "0",     # animated loop
                "-an",
                "-vsync", "0",
                "-y",
                str(output_path),
            ]
            result = await asyncio.to_thread(run_ffmpeg_sync, cmd)
            if result.returncode != 0:
                err_msg = result.stderr.decode(errors="replace").strip()
                raise Exception(f"FFmpeg error: {err_msg}")
            size = output_path.stat().st_size
            if size <= ANIMATED_MAX_BYTES:
                break
            logger.info(f"📏 Animated sticker {size // 1024} KB > limit, retrying (quality={quality}, fps={fps}, detail={detail})")
        else:
            logger.warning(f"⚠️ Animated sticker still {size // 1024} KB after lowest quality; WhatsApp may refuse to save it")
        logger.info(f"✅ Animated sticker converted! ({size // 1024} KB)")
        return str(output_path)
    except Exception as e:
        logger.error(f"❌ Animated sticker conversion failed: {e}")
        raise e


def embed_sticker_exif(webp_path: str, pack: str = "", author: str = "") -> bool:
    """Write WhatsApp sticker metadata (pack name / author) into a WebP file.

    neonize's ``passthrough`` mode (used for animated stickers) and ffmpeg's
    libwebp both skip the EXIF chunk, so pack/author were silently dropped.
    This patches the RIFF container directly: no re-encode, no webpmux needed.
    Returns True if the metadata was written.
    """
    if not (pack or author):
        return False
    from neonize.utils.sticker import add_exif

    data = bytearray(Path(webp_path).read_bytes())
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        logger.warning("⚠️ Cannot embed EXIF: not a RIFF/WebP file")
        return False

    # Locate VP8X (extended header) and drop any existing EXIF chunk.
    pos, vp8x, chunks = 12, None, []
    while pos + 8 <= len(data):
        tag = bytes(data[pos:pos + 4])
        size = int.from_bytes(data[pos + 4:pos + 8], "little")
        end = pos + 8 + size + (size & 1)
        if tag == b"VP8X":
            vp8x = len(chunks)
        if tag != b"EXIF":
            chunks.append(bytes(data[pos:end]))
        pos = end
    if vp8x is None:
        logger.warning("⚠️ Cannot embed EXIF: WebP has no VP8X chunk")
        return False

    head = bytearray(chunks[vp8x])
    head[8] |= 0x08  # EXIF flag
    chunks[vp8x] = bytes(head)

    exif = add_exif(pack or "", author or "")
    chunks.append(b"EXIF" + len(exif).to_bytes(4, "little") + exif + (b"\x00" if len(exif) & 1 else b""))

    body = b"WEBP" + b"".join(chunks)
    Path(webp_path).write_bytes(b"RIFF" + len(body).to_bytes(4, "little") + body)
    return True
