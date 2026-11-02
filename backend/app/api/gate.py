"""Invariant Drift Gate API endpoints (DRIFT-01, DRIFT-02, DRIFT-03)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import Purchase
from app.drift.models import GateEvaluation
from app.fulfillment.service import FulfillmentService

router = APIRouter(tags=["gate"])


@router.get("/purchases/{purchase_id}/gate", response_model=GateEvaluation)
async def get_gate_evaluation(
    purchase_id: str,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Retrieve the current deterministic Invariant Gate evaluation for a purchase."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    service = FulfillmentService(db=db, clock=clock)
    gate = service.reevaluate_gate(purchase_id)
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No receipt available for purchase {purchase_id} to evaluate gate",
        )
    return gate

