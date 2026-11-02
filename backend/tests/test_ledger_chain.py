"""Tests for append-only, tamper-evident hash-chained decision ledger (LEDG-01)."""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from app.core.clock import FixedClock
from app.core.models import DecisionEvent, Purchase
from app.ledger.events import GENESIS_PREV_HASH, append_event
from app.ledger.verify import verify_chain


@pytest.fixture
def purchase(db_session: Session) -> Purchase:
    p = Purchase(ref="PURCH-LEDG-01", buyer_instruction="Audit test", status="draft")
    db_session.add(p)
    db_session.commit()
    return p


def test_genesis_event_hash_chaining(db_session: Session, purchase: Purchase, fixed_clock: FixedClock):
    """Ensure first event has exactly 64 zeros as prev_hash and valid event_hash."""
    ev1 = append_event(
        session=db_session,
        purchase_id=purchase.id,
        event_type="ORDER_CREATED",
        actor="buyer",
        payload={"order_id": "ORD-001", "amount": 1000},
        clock=fixed_clock,
    )
    db_session.commit()

    assert ev1.seq == 1
    assert ev1.prev_hash == GENESIS_PREV_HASH
    assert len(ev1.event_hash) == 64

    # Second event chains to first event's event_hash
    ev2 = append_event(
        session=db_session,
        purchase_id=purchase.id,
        event_type="FUNDS_AUTHORIZED",
        actor="buyer",
        payload={"auth_id": "AUTH-001"},
        clock=fixed_clock,
    )
    db_session.commit()

    assert ev2.seq == 2
    assert ev2.prev_hash == ev1.event_hash
    assert len(ev2.event_hash) == 64
    assert ev2.event_hash != ev1.event_hash


def test_verify_chain_valid_trail(db_session: Session, purchase: Purchase, fixed_clock: FixedClock):
    """Verify clean ledger passes cryptographic audit."""
    for i in range(5):
        append_event(
            session=db_session,
            purchase_id=purchase.id,
            event_type=f"STEP_{i}",
            actor="agent",
            payload={"index": i, "status": "ok"},
            clock=fixed_clock,
        )
    db_session.commit()

    is_valid, count, broken_seq = verify_chain(db_session, purchase.id)
    assert is_valid is True
    assert count == 5
    assert broken_seq is None


def test_verify_chain_detects_payload_tampering(db_session: Session, purchase: Purchase, fixed_clock: FixedClock):
    """Verify that tampering with an event payload breaks chain verification immediately."""
    append_event(
        session=db_session,
        purchase_id=purchase.id,
        event_type="ORDER_CREATED",
        actor="buyer",
        payload={"amount": 1000},
        clock=fixed_clock,
    )
    append_event(
        session=db_session,
        purchase_id=purchase.id,
        event_type="FUNDS_CAPTURED",
        actor="agent",
        payload={"amount": 1000},
        clock=fixed_clock,
    )
    db_session.commit()

    # Verify initially valid
    is_valid, _, _ = verify_chain(db_session, purchase.id)
    assert is_valid is True

    # Tamper with event 1 payload
    ev1 = db_session.query(DecisionEvent).filter(DecisionEvent.seq == 1).first()
    assert ev1 is not None
    ev1.payload = '{"amount":999999}'
    db_session.commit()

    # Audit must detect tampering
    is_valid_after, count, broken_seq = verify_chain(db_session, purchase.id)
    assert is_valid_after is False
    assert broken_seq == 1
    assert count == 0


def test_verify_chain_empty_ledger(db_session: Session):
    """Empty ledger is trivially valid with count 0."""
    is_valid, count, broken_seq = verify_chain(db_session, "non-existent-id")
    assert is_valid is True
    assert count == 0
    assert broken_seq is None

