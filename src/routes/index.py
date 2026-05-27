from fastapi import APIRouter, Depends, Request
from src.middleware.auth import auth
from src.controllers.status.getStatus import get_status_controller, stream_status_controller
from src.controllers.status.getWelcome import get_welcome_page

router = APIRouter()

@router.get("/")
async def root_route(request: Request):
    return await get_welcome_page(request)

router.get("/status", dependencies=[Depends(auth)])(get_status_controller)

@router.get("/status/stream", dependencies=[Depends(auth)])
async def stream_status_route(request: Request):
    return await stream_status_controller(request)
