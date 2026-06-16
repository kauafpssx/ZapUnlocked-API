from fastapi import HTTPException, Request
from src.utils.decorators import require_whatsapp, handle_errors
from src.schemas import SendOptionListRequest


@require_whatsapp
@handle_errors("send option list")
async def send_option_list(data: SendOptionListRequest, request: Request):
    raise HTTPException(
        status_code=503,
        detail={
            "error": "ROUTE_DISABLED",
            "message": "This route is temporarily disabled. Option list messages are not supported on Android and iOS at this time."
        }
    )
