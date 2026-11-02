"""Verification logic for the append-only, tamper-evident decision ledger."""

from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import to_utc_iso
from app.core.models import DecisionEvent
from app.ledger.events import GENESIS_PREV_HASH, calculate_event_hash


def verify_chain(session: Session, purchase_id: str) -> Tuple[bool, int, Optional[int]]:
    """Verify cryptographic integrity of the ledger chain for a purchase.

    Returns:
        (is_valid, events_checked_count, first_invalid_seq)
        If valid: (True, count, None)
        If invalid: (False, count_verified_before_failure, failed_seq)
    """
    stmt = (
        select(DecisionEvent)
        .where(DecisionEvent.purchase_id == purchase_id)
        .order_by(DecisionEvent.seq.asc())
    )
    events = list(session.execute(stmt).scalars().all())

    if not events:
        return True, 0, None

    expected_prev_hash = GENESIS_PREV_HASH
    verified_count = 0

    for event in events:
        # Check chaining to previous hash
        if event.prev_hash != expected_prev_hash:
            return False, verified_count, event.seq

        # Recompute hash
        recorded_at_iso = to_utc_iso(event.recorded_at)
        expected_hash = calculate_event_hash(
            prev_hash=event.prev_hash,
            seq=event.seq,
            purchase_id=event.purchase_id,
            event_type=event.event_type,
            actor=event.actor,
            canonical_payload=event.payload,
            recorded_at_iso=recorded_at_iso,
        )

        if event.event_hash != expected_hash:
            return False, verified_count, event.seq

        expected_prev_hash = event.event_hash
        verified_count += 1

    return True, verified_count, None
