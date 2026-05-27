import json
import io
from PIL import Image

def add_sticker_metadata(input_path: str, pack: str, author: str) -> bytes:
    """
    Adds WhatsApp sticker metadata (Exif) to a WebP file.
    """
    img = Image.open(input_path)
    
    metadata = {
        "sticker-pack-id": "zapunlocked-api-pack",
        "sticker-pack-name": pack or "ZapUnlocked",
        "sticker-pack-publisher": author or "ZapUnlocked",
        "android-app-store-link": "https://play.google.com/store/apps/details?id=com.whatsapp",
        "ios-app-store-link": "https://itunes.apple.com/app/whatsapp-messenger/id310633997",
        "emojis": ["📦"] 
    }
    
    # Correct Exif header for WebP stickers in WhatsApp
    # Reference: https://github.com/Daliul/whatsapp-sticker-metadata-exif
    json_data = json.dumps(metadata)
    
    # The Exif chunk in a WebP file for WhatsApp stickers follows a very specific format:
    # 0-3: 'Exif'
    # 4-5: 0x00 0x00
    # 6-13: Standard TIFF header (Little Endian)
    # 14-25: Image File Directory (IFD0) entries point to the metadata string
    
    # A more common and simpler way to do this that is widely supported:
    # We wrap the JSON in a specific byte sequence that WhatsApp's parser looks for.
    
    # 0x45 0x78 0x69 0x66 0x00 0x00 (Exif\0\0)
    # 0x49 0x49 0x2A 0x00 (TIFF Little Endian)
    # ... then some length markers and the JSON
    
    exif_header = b'Exif\x00\x00II\x2a\x00\x08\x00\x00\x00\x01\x00\x41\x57\x07\x00'
    
    json_bytes = json_data.encode('utf-8')
    len_json = len(json_bytes)
    
    # Length of JSON (4 bytes, little-endian)
    len_bytes = len_json.to_bytes(4, 'little')
    
    # Full header: Exif\0\0 + TIFF + IFD entry markers + length + JSON
    # This specific sequence is known to work with most WhatsApp clients.
    full_exif = exif_header + len_bytes + b'\x00\x00\x00\x00' + json_bytes
    
    output = io.BytesIO()
    # Note: Pillow's save with exif=... will handle the WebP chunk wrapping.
    img.save(output, format='WebP', exif=full_exif, save_all=True)
    return output.getvalue()
