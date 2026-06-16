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
from src.controllers.status.logsController import get_logs, list_log_files
from src.services.logs_cleanup import run_logs_cleanup
from src.controllers.status.statsController import (
    get_stats, delete_stats,
    get_webhook_stats_controller, delete_webhook_stats_controller,
)

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
router.get("/logs/files", dependencies=[Depends(auth)])(list_log_files)
router.get("/logs", dependencies=[Depends(auth)])(get_logs)

@router.post("/logs/cleanup", dependencies=[Depends(auth)])
async def logs_cleanup_route():
    result = await run_logs_cleanup()
    return {"success": True, **result}
router.get("/stats", dependencies=[Depends(auth)])(get_stats)
router.delete("/stats", dependencies=[Depends(auth)])(delete_stats)

@router.get("/stats/webhooks", dependencies=[Depends(auth)])
async def stats_webhooks_all(request: Request):
    return await get_webhook_stats_controller(request)

@router.get("/stats/webhooks/{name}", dependencies=[Depends(auth)])
async def stats_webhooks_one(request: Request, name: str):
    return await get_webhook_stats_controller(request, name)

@router.delete("/stats/webhooks", dependencies=[Depends(auth)])
async def delete_stats_webhooks_all(request: Request):
    return await delete_webhook_stats_controller(request)

@router.delete("/stats/webhooks/{name}", dependencies=[Depends(auth)])
async def delete_stats_webhooks_one(request: Request, name: str):
    return await delete_webhook_stats_controller(request, name)

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
