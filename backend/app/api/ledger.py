"""Decision ledger audit replay and cryptographic verification endpoints."""

import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import DecisionEvent, Purchase
from app.ledger.verify import verify_chain

router = APIRouter(prefix="/purchases", tags=["ledger"])


class LedgerEventItem(BaseModel):
    seq: int
    purchase_id: str
    event_type: str
    actor: str
    payload: Any
    prev_hash: str
    event_hash: str
    recorded_at: str


class ReplayResponse(BaseModel):
    purchase_id: str
    events_count: int
    events: List[LedgerEventItem]


class VerifyResponse(BaseModel):
    purchase_id: str
    verified: bool
    events_checked: int
    broken_seq: Optional[int] = None


@router.get("/{purchase_id}/replay", response_model=ReplayResponse)
async def replay_ledger(
    purchase_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve full append-only audit trail for a purchase in sequence order."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    stmt = (
        select(DecisionEvent)
        .where(DecisionEvent.purchase_id == purchase_id)
        .order_by(DecisionEvent.seq.asc())
    )
    events = db.execute(stmt).scalars().all()

    items = []
    for ev in events:
        try:
            parsed_payload = json.loads(ev.payload)
        except Exception:
            parsed_payload = ev.payload

        items.append(
            LedgerEventItem(
                seq=ev.seq,
                purchase_id=ev.purchase_id,
                event_type=ev.event_type,
                actor=ev.actor,
                payload=parsed_payload,
                prev_hash=ev.prev_hash,
                event_hash=ev.event_hash,
                recorded_at=ev.recorded_at.isoformat(),
            )
        )

    return ReplayResponse(
        purchase_id=purchase_id,
        events_count=len(items),
        events=items,
    )


@router.post("/{purchase_id}/verify", response_model=VerifyResponse)
async def verify_ledger(
    purchase_id: str,
    db: Session = Depends(get_db),
):
    """Verify cryptographic SHA-256 chain continuity for a purchase ledger."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    is_valid, checked_count, broken_seq = verify_chain(session=db, purchase_id=purchase_id)

    return VerifyResponse(
        purchase_id=purchase_id,
        verified=is_valid,
        events_checked=checked_count,
        broken_seq=broken_seq,
    )

