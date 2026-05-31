from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.qr.getQRPage import get_qr_page
from src.controllers.whatsapp.qr.getQRImage import get_qr_image

router = APIRouter(dependencies=[Depends(auth)])

router.get("/")(get_qr_page)
router.get("/image")(get_qr_image)
