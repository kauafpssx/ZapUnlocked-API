from fastapi import APIRouter, Depends, Body
from typing import Dict, Any
from src.middleware.auth import auth
from src.controllers.system.envController import get_env_vars, update_env_vars
from src.controllers.system.cleanupController import (
    force_cleanup,
    get_cleanup_settings,
    update_cleanup_settings,
)

router = APIRouter(dependencies=[Depends(auth)])

router.get("/env")(get_env_vars)

@router.put("/env")
async def update_env_route(env_data: Dict[str, str] = Body(...)):
    return await update_env_vars(env_data)

router.post("/cleanup/force")(force_cleanup)
router.get("/cleanup/settings")(get_cleanup_settings)

@router.put("/cleanup/settings")
async def update_cleanup_route(settings: Dict[str, Any] = Body(...)):
    return await update_cleanup_settings(settings)
