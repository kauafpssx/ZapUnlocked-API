from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.contacts.contactController import get_contact_info

router = APIRouter(dependencies=[Depends(auth)])

router.post("/info")(get_contact_info)
