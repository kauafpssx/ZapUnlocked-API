from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.send.sendForm import send_form

router = APIRouter(dependencies=[Depends(auth)])

router.post("/messages/send-form")(send_form)