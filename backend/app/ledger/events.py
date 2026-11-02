"""Hash-chained, tamper-evident append-only ledger events."""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import canonical_json, sha256_hex, to_utc_iso
from app.core.clock import Clock, SystemClock
from app.core.models import DecisionEvent

GENESIS_PREV_HASH = "0" * 64


def calculate_event_hash(
    prev_hash: str,
    seq: int,
    purchase_id: str,
    event_type: str,
    actor: str,
    canonical_payload: str,
    recorded_at_iso: str,
) -> str:
    """Compute cryptographic SHA-256 digest over ledger event tuple."""
    raw = f"{prev_hash}:{seq}:{purchase_id}:{event_type}:{actor}:{canonical_payload}:{recorded_at_iso}"
    return sha256_hex(raw)


def append_event(
    session: Session,
    purchase_id: str,
    event_type: str,
    actor: str,
    payload: dict[str, Any],
    clock: Optional[Clock] = None,
) -> DecisionEvent:
    """Append a new tamper-evident event to the purchase decision ledger.

    Atomically chains to the previous event hash. If no previous event exists,
    uses 64 zeros as genesis hash.
    """
    clk = clock or SystemClock()
    now_dt = clk.now()
    recorded_at_iso = to_utc_iso(now_dt)

    # Query last event for this purchase with ordering by seq desc
    stmt = (
        select(DecisionEvent)
        .where(DecisionEvent.purchase_id == purchase_id)
        .order_by(DecisionEvent.seq.desc())
        .limit(1)
    )
    prev_event = session.execute(stmt).scalars().first()

    if prev_event is None:
        next_seq = 1
        prev_hash = GENESIS_PREV_HASH
    else:
        next_seq = prev_event.seq + 1
        prev_hash = prev_event.event_hash

    canon_payload = canonical_json(payload)
    event_hash = calculate_event_hash(
        prev_hash=prev_hash,
        seq=next_seq,
        purchase_id=purchase_id,
        event_type=event_type,
        actor=actor,
        canonical_payload=canon_payload,
        recorded_at_iso=recorded_at_iso,
    )

    event = DecisionEvent(
        seq=next_seq,
        purchase_id=purchase_id,
        event_type=event_type,
        actor=actor,
        payload=canon_payload,
        prev_hash=prev_hash,
        event_hash=event_hash,
        recorded_at=now_dt,
    )
    session.add(event)
    session.flush()
    return event
