import asyncio
from fastapi import HTTPException
from pydantic import BaseModel
from src.utils.decorators import handle_errors
from src.services.sessions.registry import (
    list_sessions, get_session, create_session,
    rename_session, delete_session, get_active_sessions,
)


class CreateSessionBody(BaseModel):
    name: str | None = None


class RenameSessionBody(BaseModel):
    name: str


@handle_errors("list sessions")
async def list_sessions_handler():
    return {"success": True, "sessions": list_sessions()}


@handle_errors("create session")
async def create_session_handler(body: CreateSessionBody):
    session = create_session(body.name)
    return {"success": True, "session": session}


@handle_errors("rename session")
async def rename_session_handler(session_id: str, body: RenameSessionBody):
    try:
        session = rename_session(session_id, body.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "session": session}


@handle_errors("delete session")
async def delete_session_handler(session_id: str):
    try:
        delete_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"success": True, "message": f"Session '{session_id}' deactivated."}


@handle_errors("connect session")
async def connect_session_handler(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    from src.services.whatsapp.client import start_bot
    from src.services.whatsapp import state

    # set_keep_qr_active_on_restart survives the reset_for_reconnect() call inside
    # start_bot(), which zeros out qr_generation_active before the QR event fires
    state.set_keep_qr_active_on_restart(True, session_id)

    # This handler already runs on the uvicorn event loop, so create_task is enough.
    # The previous call_soon_threadsafe + loop-search approach was not needed and
    # could silently drop the task if no other session had a loop yet.
    asyncio.create_task(start_bot(session_id))

    return {"success": True, "message": f"Session '{session_id}' connecting..."}


@handle_errors("disconnect session")
async def disconnect_session_handler(session_id: str):
    from src.services.whatsapp import state
    client = state.get_client(session_id)
    if client:
        try:
            loop = state.get_main_loop(session_id)
            if loop:
                await asyncio.get_event_loop().run_in_executor(None, client.disconnect)
        except Exception:
            pass
    state.mark_disconnected(session_id)
    return {"success": True, "message": f"Session '{session_id}' disconnected."}


@handle_errors("session status")
async def session_status_handler(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    from src.services.whatsapp import state
    is_ready = state.get_is_ready(session_id)
    qr = state.get_qr(session_id) is not None
    return {
        "success": True,
        "sessionId": session_id,
        "name": session.get("name"),
        "connected": is_ready,
        "hasQr": qr,
    }
