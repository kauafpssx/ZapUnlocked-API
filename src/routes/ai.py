from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.ai.chatController import ask_controller, imagine_controller

router = APIRouter(dependencies=[Depends(auth)])

router.post("/ask")(ask_controller)
router.post("/imagine")(imagine_controller)
