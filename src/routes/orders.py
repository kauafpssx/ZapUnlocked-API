from fastapi import APIRouter, Depends
from src.middleware.auth import auth
from src.controllers.whatsapp.orders.ordersController import (
    list_orders,
    get_order,
    create_order,
    refresh_order,
    patch_order,
    accept_order,
    decline_order,
    payment_info,
    review_and_pay,
)

router = APIRouter(dependencies=[Depends(auth)])

router.post("/orders")(create_order)
router.get("/orders")(list_orders)
router.get("/orders/{order_id}")(get_order)
router.post("/orders/{order_id}/refresh")(refresh_order)
router.patch("/orders/{order_id}")(patch_order)
router.post("/orders/{order_id}/accept")(accept_order)
router.post("/orders/{order_id}/decline")(decline_order)
router.post("/orders/{order_id}/payment-info")(payment_info)
router.post("/orders/{order_id}/review-and-pay")(review_and_pay)