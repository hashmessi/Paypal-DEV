"""Checkout and Order creation endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock, get_gateway
from app.core.clock import Clock
from app.core.db import get_db
from app.payments.port import PaymentGateway
from app.payments.service import PaymentsService
from app.payments.state import PaymentStateError

router = APIRouter(prefix="/checkout", tags=["checkout"])


class CreateOrderRequest(BaseModel):
    ref: str = Field(..., description="Purchase reference string", json_schema_extra={"example": "ORD-7892"})
    amount_cents: int = Field(..., description="Amount in integer minor units (e.g. 8999 for $89.99)", ge=1)
    currency: str = Field(default="USD", max_length=3)
    buyer_instruction: str = Field(default="Autonomous research purchase", description="Buyer terms")
    receipt_hash: Optional[str] = Field(None, description="Cryptographic Promise Receipt hash bound to order (PAY-08)")
    return_url: str = Field(default="https://promiseloop.dev/checkout/return")
    cancel_url: str = Field(default="https://promiseloop.dev/checkout/cancel")


class CreateOrderResponse(BaseModel):
    purchase_id: str
    order_id: str
    status: str
    approval_url: str


class AuthorizeOrderResponse(BaseModel):
    authorization_id: str
    order_id: str
    state: str
    amount_cents: int
    currency: str
    expiration_time: Optional[str] = None
    honor_until: Optional[str] = None


@router.post("/orders", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Create a new purchase order with intent=AUTHORIZE on PayPal."""
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    try:
        result = await service.create_checkout_order(
            purchase_ref=req.ref,
            amount_cents=req.amount_cents,
            currency=req.currency,
            buyer_instruction=req.buyer_instruction,
            receipt_hash=req.receipt_hash,
            return_url=req.return_url,
            cancel_url=req.cancel_url,
        )
        return result
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order creation failed: {str(err)}",
        )


@router.post("/orders/{order_id}/authorize", response_model=AuthorizeOrderResponse)
async def authorize_order(
    order_id: str,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Authorize an approved PayPal order, placing hold on buyer funds."""
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    try:
        auth = await service.authorize_order(order_id=order_id)
        return {
            "authorization_id": auth.authorization_id or "",
            "order_id": auth.order_id or "",
            "state": auth.state,
            "amount_cents": auth.amount_cents,
            "currency": auth.currency,
            "expiration_time": auth.expiration_time.isoformat() if auth.expiration_time else None,
            "honor_until": auth.honor_until.isoformat() if auth.honor_until else None,
        }
    except PaymentStateError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authorization failed: {str(err)}",
        )
