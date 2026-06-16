from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.sessions.sessionsController import (
    list_sessions_handler,
    create_session_handler,
    rename_session_handler,
    delete_session_handler,
    connect_session_handler,
    disconnect_session_handler,
    session_status_handler,
)

router = APIRouter(dependencies=[Depends(auth)])

router.get("/sessions")(list_sessions_handler)
router.post("/sessions")(create_session_handler)
router.put("/sessions/{session_id}/rename")(rename_session_handler)
router.delete("/sessions/{session_id}")(delete_session_handler)
router.post("/sessions/{session_id}/connect")(connect_session_handler)
router.post("/sessions/{session_id}/disconnect")(disconnect_session_handler)
router.get("/sessions/{session_id}/status")(session_status_handler)
