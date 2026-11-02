"""Payments lifecycle endpoints: capture, void, and reconcile."""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock, get_gateway
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import Purchase
from app.payments.port import PaymentGateway
from app.payments.service import PaymentsService
from app.payments.state import (
    CaptureBlockedByGateError,
    PaymentStateError,
    TerminalStateError,
)

router = APIRouter(prefix="/purchases", tags=["payments"])


class CaptureRequest(BaseModel):
    amount_cents: Optional[int] = Field(None, description="Optional partial capture amount in cents", ge=1)
    note: str = Field(default="Agent executed promise verified", description="Audit note")
    actor: str = Field(default="agent", description="Actor triggering capture")


class VoidRequest(BaseModel):
    reason: str = Field(default="Buyer requested cancellation", description="Void reason")
    actor: str = Field(default="buyer", description="Actor triggering void")


@router.get("/{purchase_id}")
async def get_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Retrieve purchase and authorization state."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    auth = service.get_authorization_by_purchase_id(purchase_id)

    return {
        "id": purchase.id,
        "ref": purchase.ref,
        "status": purchase.status,
        "buyer_instruction": purchase.buyer_instruction,
        "created_at": purchase.created_at.isoformat(),
        "authorization": {
            "id": auth.id,
            "order_id": auth.order_id,
            "authorization_id": auth.authorization_id,
            "state": auth.state,
            "amount_cents": auth.amount_cents,
            "currency": auth.currency,
            "expiration_time": auth.expiration_time.isoformat() if auth.expiration_time else None,
            "honor_until": auth.honor_until.isoformat() if auth.honor_until else None,
            "capture_id": auth.capture_id,
            "captured_at": auth.captured_at.isoformat() if auth.captured_at else None,
            "voided_at": auth.voided_at.isoformat() if auth.voided_at else None,
            "void_reason": auth.void_reason,
        } if auth else None,
    }


@router.post("/{purchase_id}/capture")
async def capture_purchase(
    purchase_id: str,
    req: CaptureRequest = CaptureRequest(),
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Capture authorized funds.

    Guarantees:
    - PAY-04: Rejects calls on terminal states (captured, voided, expired, failed) with 409 Conflict without contacting PayPal.
    - PAY-05: Enforces deterministic idempotency using PayPal-Request-Id header.
    - LEDG-01: Appends FUNDS_CAPTURED event to hash-chained ledger.
    """
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    try:
        result = await service.capture_authorization(
            purchase_id=purchase_id,
            amount_cents=req.amount_cents,
            note=req.note,
            actor=req.actor,
        )
        return result
    except CaptureBlockedByGateError as err:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "CAPTURE_BLOCKED_BY_GATE", "message": str(err), "outcome": err.outcome, "findings": err.findings},
        )
    except TerminalStateError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except PaymentStateError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Capture failed: {str(err)}",
        )


@router.post("/{purchase_id}/void")
async def void_purchase(
    purchase_id: str,
    req: VoidRequest = VoidRequest(),
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Void authorized funds, releasing hold back to buyer."""
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    try:
        result = await service.void_authorization(
            purchase_id=purchase_id,
            reason=req.reason,
            actor=req.actor,
        )
        return result
    except TerminalStateError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except PaymentStateError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Void failed: {str(err)}",
        )


@router.post("/{purchase_id}/reconcile")
async def reconcile_purchase(
    purchase_id: str,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Reconcile local authorization state against remote PayPal status."""
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    try:
        result = await service.reconcile_authorization(purchase_id=purchase_id)
        return result
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation failed: {str(err)}",
        )

