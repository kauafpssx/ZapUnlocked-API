from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from src.middleware.auth import auth
from src.controllers.status.getStatus import get_status_controller, stream_status_controller
from src.controllers.status.getWelcome import get_welcome_page
from src.controllers.status.healthController import health_controller
from src.controllers.status.readinessController import readiness_controller
from src.controllers.status.memoryController import get_memory_status
from src.controllers.status.volumeController import get_volume_status
from src.controllers.status.logsController import get_logs

router = APIRouter()

@router.get("/")
async def root_route(request: Request):
    return await get_welcome_page(request)

router.get("/status", dependencies=[Depends(auth)])(get_status_controller)

@router.get("/status/stream", dependencies=[Depends(auth)])
async def stream_status_route(request: Request):
    return await stream_status_controller(request)

router.get("/status/health")(health_controller)
router.get("/status/readiness")(readiness_controller)
router.get("/status/memory", dependencies=[Depends(auth)])(get_memory_status)
router.get("/status/volume", dependencies=[Depends(auth)])(get_volume_status)
router.get("/logs", dependencies=[Depends(auth)])(get_logs)

_COLLECTION_PATH = Path(__file__).resolve().parents[2] / "ZapUnlocked.collection.json"

@router.get("/collection.json")
async def get_collection():
    if not _COLLECTION_PATH.exists():
        raise HTTPException(status_code=404, detail="Collection file not found.")
    return FileResponse(_COLLECTION_PATH, media_type="application/json")

@router.post("/collection.json", dependencies=[Depends(auth)])
async def update_collection(request: Request):
    body = await request.body()
    _COLLECTION_PATH.write_bytes(body)
    return {"success": True, "message": "Collection updated."}
