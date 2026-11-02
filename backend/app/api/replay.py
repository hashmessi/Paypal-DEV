"""Promise Replay 10-step timeline and audit endpoint (UI-03, LEDG-02)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import Purchase
from app.replay.models import ReplayData
from app.replay.service import ReplayService

router = APIRouter(tags=["replay"])


@router.get("/purchases/{purchase_id}/replay-timeline", response_model=ReplayData)
@router.get("/purchases/{purchase_id}/replay", response_model=ReplayData)
async def get_replay_timeline(
    purchase_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve the full 10-step lifecycle replay with divergence detection and ledger chain integrity."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    service = ReplayService(db=db)
    return service.get_replay_timeline(purchase_id)

