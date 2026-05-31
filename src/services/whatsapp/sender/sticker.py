from src.services.whatsapp.sender.helpers import _ensure_client, _build_message_info, _save_to_history, build_jid, _dispatch_sent_event


async def send_sticker_message(jid: str, sticker_path: str, pack: str = "", author: str = "", options: dict = None):
    client = _ensure_client()

    res = client.send_sticker(
        to=build_jid(jid),
        file=sticker_path,
        name=pack,
        packname=author,
        passthrough=False,
        quoted=_build_message_info(options.get("quoted")) if options else None
    )

    await _save_to_history(jid, {"stickerMessage": {}}, res)
    await _dispatch_sent_event(jid, "sticker", res)
    return res
