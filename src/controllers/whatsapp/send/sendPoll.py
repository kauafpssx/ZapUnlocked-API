from fastapi import HTTPException
from src.services.whatsapp.client import get_is_ready
from src.services.whatsapp.sender import send_poll_message, send_poll_vote_message, find_message
from src.utils.logger import logger
from src.utils.quote import resolve_quote
from ..schemas import SendPollRequest, SendPollVoteRequest

async def send_poll(data: SendPollRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        options_dict = await resolve_quote(
            jid,
            reply_identifier=data.reply or data.quoted_id,
            reply_type=data.type or "id",
        )

        if not data.options or len(data.options) < 2:
            raise HTTPException(status_code=400, detail={"error": "INVALID_FIELD", "message": "A poll must have at least 2 options."})
            
        await send_poll_message(
            jid, 
            name=data.name, 
            options=data.options, 
            selectable_count=data.selectableCount or 1,
            message_options=options_dict
        )
        return {"success": True, "message": "Poll sent."}
    except Exception as e:
        logger.error(f"❌ Erro ao enviar enquete: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})

async def send_poll_vote(data: SendPollVoteRequest):
    if not get_is_ready():
        raise HTTPException(status_code=503, detail={"error": "WHATSAPP_NOT_CONNECTED", "message": "WhatsApp is not connected."})

    try:
        jid = f"{data.phone}@s.whatsapp.net"

        if not data.options:
            raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "At least one option must be selected to vote."})
        
        poll_id = data.pollId
        poll_name = data.pollName or "Poll"
        from_me = False
        timestamp = 0
        target_type = data.type or "id"

        logger.debug(f"🗳️ Starting vote for {jid}: type={target_type}, pollId={data.pollId}, options={data.options}")

        if target_type == "text":
            search_query = data.pollId or data.pollName
            logger.debug(f"🗳️ Buscando enquete por texto: '{search_query}'")

            if not search_query:
                raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "'pollId' or 'pollName' is required to search by text."})

            found_msg = await find_message(jid, search_query, target_type)
            if not found_msg:
                raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Poll not found by text: {search_query}"})

            poll_id = found_msg["key"]["id"]
            from_me = found_msg["key"].get("fromMe", False)
            timestamp = found_msg.get("messageTimestamp", 0)

            if "message" in found_msg and "pollCreationMessage" in found_msg["message"]:
                poll_name = found_msg["message"]["pollCreationMessage"].get("name", poll_name)

        logger.debug(f"🗳️ Sending vote: ID={poll_id}, options={data.options}, fromMe={from_me}")

        await send_poll_vote_message(
            jid, 
            poll_id=poll_id,
            poll_name=poll_name,
            options=data.options,
            from_me=from_me,
            timestamp=timestamp
        )
        return {"success": True, "message": "Poll vote sent."}
    except Exception as e:
        logger.error(f"❌ Failed to send poll vote: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail={"error": "INTERNAL_ERROR", "message": str(e)})
