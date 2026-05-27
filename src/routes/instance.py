from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.settings.instanceInfoController import get_instance_me, get_instance_device
from src.controllers.whatsapp.settings.instanceSettingsController import update_instance_name

router = APIRouter(dependencies=[Depends(auth)])

router.get("/me")(get_instance_me)
router.get("/device")(get_instance_device)
router.put("/update-name")(update_instance_name)
