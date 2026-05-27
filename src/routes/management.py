from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.management.fetchMessages import fetch_messages
from src.controllers.whatsapp.management.getRecentChats import get_recent_chats
from src.controllers.system.getMemoryStats import get_memory_stats
from src.controllers.system.getVolumeStats import get_volume_stats
from src.controllers.system.clearStorage import clear_storage
from src.controllers.whatsapp.management.databaseController import manual_cleanup, update_config, get_status

router = APIRouter(dependencies=[Depends(auth)])

router.post("/fetch_messages")(fetch_messages)
router.post("/recent_contacts")(get_recent_chats)
router.get("/memory")(get_memory_stats)
router.get("/volume_stats")(get_volume_stats)
router.delete("/cleanup")(clear_storage)

# Database Management
router.post("/database/cleanup")(manual_cleanup)
router.post("/database/config")(update_config)
router.get("/database/status")(get_status)
