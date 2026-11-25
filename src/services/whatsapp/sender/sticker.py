import asyncio
from src.services.whatsapp.sender.helpers import _ensure_client, _build_message_info, _save_to_history, build_jid, _dispatch_sent_event, apply_pre_send


async def send_sticker_message(jid: str, sticker_path: str, pack: str = "", author: str = "", options: dict = None, passthrough: bool = False, audio_path: str = None, session_id: str = "1"):
    client = _ensure_client(session_id)
    await apply_pre_send(jid, options, client)

    quoted = _build_message_info(options.get("quoted")) if options else None

    def _send():
        sticker_msg = client.build_sticker_message(
            file=sticker_path,
            name=pack,
            packname=author,
            passthrough=passthrough,
            quoted=quoted,
        )
        if audio_path:
            audio_msg = client.build_audio_message(audio_path)
            try:
                sticker_msg.stickerMessage.audioMessage.CopyFrom(audio_msg.audioMessage)
            except Exception:
                pass
        return client.send_message(
            to=build_jid(jid),
            message=sticker_msg,
        )

    res = await asyncio.wait_for(asyncio.to_thread(_send), timeout=60)

    content = {"stickerMessage": {}}
    if audio_path:
        content["stickerMessage"]["audioMessage"] = {}
    await _save_to_history(jid, content, res, session_id)
    await _dispatch_sent_event(jid, "sticker", res, session_id)
    return res
