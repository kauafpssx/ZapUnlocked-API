import gc

from src.services.whatsapp.sender.helpers import _ensure_client, _build_context_info, _save_to_history, build_jid, _dispatch_sent_event, apply_pre_send


async def send_image_message(jid: str, image_path: str, caption: str = "", as_document: bool = False, file_name: str = None, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, ImageMessage, DocumentMessage
    from neonize.utils.enum import MediaType
    from pathlib import Path

    client = _ensure_client()
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    mimetype = magic.from_buffer(image_bytes, mime=True)

    await apply_pre_send(jid, options, client)
    if as_document:
        upload = client.upload(image_bytes, MediaType.MediaDocument)
        final_name = file_name or Path(image_path).name or "image"
        msg = Message(
            documentMessage=DocumentMessage(
                URL=upload.url,
                directPath=upload.DirectPath,
                mediaKey=upload.MediaKey,
                fileEncSHA256=upload.FileEncSHA256,
                fileSHA256=upload.FileSHA256,
                fileLength=len(image_bytes),
                mimetype=mimetype,
                fileName=final_name,
                caption=caption,
                contextInfo=_build_context_info(options.get("quoted"), options.get("mentioned")) if options else None
            )
        )
        res = client.send_message(build_jid(jid), msg)
        await _save_to_history(jid, {"documentMessage": {"fileName": final_name, "caption": caption}}, res)
        await _dispatch_sent_event(jid, "document", res)
    else:
        upload = client.upload(image_bytes, MediaType.MediaImage)
        msg = Message(
            imageMessage=ImageMessage(
                URL=upload.url,
                directPath=upload.DirectPath,
                mediaKey=upload.MediaKey,
                fileEncSHA256=upload.FileEncSHA256,
                fileSHA256=upload.FileSHA256,
                fileLength=len(image_bytes),
                mimetype=mimetype,
                caption=caption,
                contextInfo=_build_context_info(options.get("quoted"), options.get("mentioned")) if options else None
            )
        )
        res = client.send_message(build_jid(jid), msg)
        await _save_to_history(jid, {"imageMessage": {"caption": caption}}, res)
        await _dispatch_sent_event(jid, "image", res)

    del image_bytes
    gc.collect()
    return res


async def send_audio_message(jid: str, audio_path: str, is_ptt: bool = False, duration: int = 0, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, AudioMessage
    from neonize.utils.enum import MediaType

    client = _ensure_client()
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    if audio_path.endswith(".ogg"):
        mimetype = "audio/ogg; codecs=opus"
    elif audio_path.endswith(".m4a"):
        mimetype = "audio/mp4"
    elif audio_path.endswith(".mp3"):
        mimetype = "audio/mpeg"
    elif audio_path.endswith(".wav"):
        mimetype = "audio/wav"
    else:
        mimetype = magic.from_buffer(audio_bytes, mime=True)
    await apply_pre_send(jid, options, client)
    upload = client.upload(audio_bytes, MediaType.MediaAudio)

    msg = Message(
        audioMessage=AudioMessage(
            URL=upload.url,
            directPath=upload.DirectPath,
            mediaKey=upload.MediaKey,
            fileEncSHA256=upload.FileEncSHA256,
            fileSHA256=upload.FileSHA256,
            fileLength=len(audio_bytes),
            mimetype=mimetype,
            PTT=is_ptt,
            seconds=duration,
            contextInfo=_build_context_info(options.get("quoted"), options.get("mentioned")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"audioMessage": {}}, res)
    await _dispatch_sent_event(jid, "audio", res)
    del audio_bytes
    gc.collect()
    return res


async def send_video_message(jid: str, video_path: str, caption: str = "", as_document: bool = False, gif_playback: bool = False, ptv: bool = False, options: dict = None):
    import magic
    import os
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, VideoMessage
    from neonize.utils.enum import MediaType

    client = _ensure_client()
    if as_document:
        return await send_document_message(jid, video_path, os.path.basename(video_path), options=options)

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    mimetype = magic.from_buffer(video_bytes, mime=True)
    await apply_pre_send(jid, options, client)
    upload = client.upload(video_bytes, MediaType.MediaVideo)

    video_msg = VideoMessage(
        URL=upload.url,
        directPath=upload.DirectPath,
        mediaKey=upload.MediaKey,
        fileEncSHA256=upload.FileEncSHA256,
        fileSHA256=upload.FileSHA256,
        fileLength=len(video_bytes),
        mimetype=mimetype,
        caption=caption,
        gifPlayback=gif_playback,
        contextInfo=_build_context_info(options.get("quoted"), options.get("mentioned")) if options else None
    )

    if ptv:
        msg = Message(ptvMessage=video_msg)
    else:
        msg = Message(videoMessage=video_msg)

    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"videoMessage": {"caption": caption}}, res)
    await _dispatch_sent_event(jid, "video", res)
    del video_bytes
    gc.collect()
    return res


async def send_document_message(jid: str, file_path: str, file_name: str, mimetype: str = None, options: dict = None):
    import magic
    from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, DocumentMessage
    from neonize.utils.enum import MediaType

    client = _ensure_client()
    with open(file_path, "rb") as f:
        doc_bytes = f.read()

    if not mimetype:
        mimetype = magic.from_buffer(doc_bytes, mime=True)
    await apply_pre_send(jid, options, client)
    upload = client.upload(doc_bytes, MediaType.MediaDocument)

    msg = Message(
        documentMessage=DocumentMessage(
            URL=upload.url,
            directPath=upload.DirectPath,
            mediaKey=upload.MediaKey,
            fileEncSHA256=upload.FileEncSHA256,
            fileSHA256=upload.FileSHA256,
            fileLength=len(doc_bytes),
            mimetype=mimetype,
            fileName=file_name,
            contextInfo=_build_context_info(options.get("quoted"), options.get("mentioned")) if options else None
        )
    )
    res = client.send_message(build_jid(jid), msg)
    await _save_to_history(jid, {"documentMessage": {"title": file_name}}, res)
    await _dispatch_sent_event(jid, "document", res)
    del doc_bytes
    gc.collect()
    return res
