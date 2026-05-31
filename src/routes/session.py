from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.qr.pairController import pair_device
from src.controllers.whatsapp.qr.logout import logout

router = APIRouter(dependencies=[Depends(auth)])

router.post("/pair")(pair_device)
router.post("/logout")(logout)
