"""Orders controllers."""

from fastapi import HTTPException, Query, Request

from src.utils.decorators import handle_errors, get_session_id
from src.services.whatsapp import orders as order_service
from src.services.whatsapp import payments as payment_service
from src.schemas.orders import OrderPatchRequest, OrderCreateRequest
from src.schemas.payments import PaymentInfoRequest, ReviewAndPayRequest


@handle_errors("create order")
async def create_order(data: OrderCreateRequest, request: Request):
    sid = get_session_id(request)
    created = await order_service.create_order(sid, data)
    return created


@handle_errors("list orders")
async def list_orders(
    request: Request,
    phone: str = Query(default=None),
    status: str = Query(default=None),
    localStatus: str = Query(default=None),
    currency: str = Query(default=None),
    dateFrom: str = Query(default=None),
    dateTo: str = Query(default=None),
    limit: int = Query(default=50),
    offset: int = Query(default=0),
):
    sid = get_session_id(request)
    return order_service.list_orders(
        sid,
        phone=phone,
        status=status,
        local_status=localStatus,
        currency=currency,
        date_from=dateFrom,
        date_to=dateTo,
        limit=limit,
        offset=offset,
    )


@handle_errors("get order")
async def get_order(order_id: str, request: Request):
    sid = get_session_id(request)
    order = order_service.get_order(sid, order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    return order


@handle_errors("refresh order")
async def refresh_order(order_id: str, request: Request):
    sid = get_session_id(request)
    result = await order_service.refresh_order(sid, order_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail={"error": "ORDER_REFRESH_FAILED", "message": result.get("error", "Failed.")})
    return result


@handle_errors("patch order")
async def patch_order(order_id: str, data: OrderPatchRequest, request: Request):
    sid = get_session_id(request)
    patch = data.model_dump(exclude_none=True)
    updated = await order_service.update_order(sid, order_id, patch)
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    return updated


@handle_errors("accept order")
async def accept_order(order_id: str, request: Request):
    sid = get_session_id(request)
    updated = await order_service.update_order(sid, order_id, {"local_status": "accepted"})
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    return {"success": True, "orderId": order_id, "localStatus": "accepted"}


@handle_errors("decline order")
async def decline_order(order_id: str, request: Request):
    sid = get_session_id(request)
    updated = await order_service.update_order(sid, order_id, {"local_status": "declined"})
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    return {"success": True, "orderId": order_id, "localStatus": "declined"}


@handle_errors("payment info")
async def payment_info(order_id: str, data: PaymentInfoRequest, request: Request):
    sid = get_session_id(request)
    order = order_service.get_order(sid, order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    jid = data.phone or order.get("chat_jid")
    if not jid:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "phone or order chat is required."})
    res, ref = await payment_service.send_payment_info(sid, jid, data)
    return {"success": True, "orderId": order_id, "referenceId": ref, "messageId": getattr(res, "ID", None)}


@handle_errors("review and pay")
async def review_and_pay(order_id: str, data: ReviewAndPayRequest, request: Request):
    sid = get_session_id(request)
    order = order_service.get_order(sid, order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"error": "ORDER_NOT_FOUND", "message": "Order not found."})
    jid = data.phone or order.get("chat_jid")
    if not jid:
        raise HTTPException(status_code=400, detail={"error": "MISSING_FIELD", "message": "phone or order chat is required."})
    res, ref = await payment_service.send_review_and_pay(sid, jid, data)
    return {"success": True, "orderId": order_id, "referenceId": ref, "messageId": getattr(res, "ID", None)}