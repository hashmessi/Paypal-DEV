"""Tests for Promise Replay 10-step timeline and chain audit (UI-03, LEDG-02)."""

from datetime import datetime, timedelta, timezone
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import FixedClock
from app.core.models import (
    Base,
    DecisionEvent,
    GateEvaluationRecord,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.fulfillment.models import IngestEvidenceRequest
from app.fulfillment.service import FulfillmentService
from app.ledger.events import append_event
from app.replay.service import ReplayService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def populated_purchase(db_session: Session):
    clock = FixedClock(datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc))

    purchase = Purchase(
        ref="PUR-REPLAY-01",
        buyer_instruction="Buy Sony WH-1000XM5 under $400 new in black",
        status="authorized",
    )
    db_session.add(purchase)
    db_session.flush()

    # Step 1: Buyer Instruction event
    append_event(db_session, purchase.id, "INSTRUCTION_SUBMITTED", "buyer", {"instruction": purchase.buyer_instruction}, clock)

    # Step 2: Constraints Extracted
    append_event(db_session, purchase.id, "INTENT_EXTRACTED", "intent_extractor", {"brand": "Sony", "model": "WH-1000XM5", "max_budget_cents": 40000}, clock)

    # Step 3: Candidate Selected
    append_event(db_session, purchase.id, "PRODUCT_SELECTED", "discovery_engine", {"sku": "WH1000XM5-BLK-NEW", "title": "Sony WH-1000XM5 Wireless Headphones"}, clock)

    # Step 4: Quote Confirmed
    append_event(db_session, purchase.id, "QUOTE_CONFIRMED", "merchant_gateway", {"total_cents": 39900, "currency": "USD"}, clock)

    # Step 5: Receipt Compiled
    conditions = {
        "expected_sku": "WH1000XM5-BLK-NEW",
        "expected_color": "black",
        "reject_refurbished": True,
        "max_delivery_days": 5,
    }
    receipt = PromiseReceipt(
        purchase_id=purchase.id,
        version=1,
        receipt_hash="r" * 64,
        status="approved",
        canonical_payload="{}",
        constraints_json=json.dumps({"max_budget_cents": 40000, "allow_refurbished": False}),
        product_snapshot_json=json.dumps({"title": "Sony WH-1000XM5", "sku": "WH1000XM5-BLK-NEW", "color": "black"}),
        merchant_quote_json=json.dumps({"item_cents": 39900, "shipping_cents": 0, "tax_cents": 0, "total_cents": 39900, "currency": "USD"}),
        capture_conditions_json=json.dumps(conditions),
        total_cents=39900,
        currency="USD",
        created_at=clock.now(),
    )
    db_session.add(receipt)
    append_event(db_session, purchase.id, "RECEIPT_COMPILED", "receipt_compiler", {"receipt_hash": receipt.receipt_hash, "version": 1}, clock)

    # Step 6: Receipt Approved
    append_event(db_session, purchase.id, "RECEIPT_APPROVED", "buyer", {"receipt_hash": receipt.receipt_hash}, clock)

    # Step 7: PayPal Hold Authorized
    auth = PaymentAuthorization(
        purchase_id=purchase.id,
        authorization_id="AUTH-REPLAY-01",
        order_id="ORDER-REPLAY-01",
        state="authorized",
        amount_cents=39900,
        currency="USD",
        expiration_time=clock.now() + timedelta(days=29),
        created_at=clock.now(),
    )
    db_session.add(auth)
    append_event(db_session, purchase.id, "FUNDS_AUTHORIZED", "buyer", {"authorization_id": auth.authorization_id, "amount_cents": 39900}, clock)

    db_session.commit()
    return purchase, receipt, auth, clock


def test_replay_10_steps_happy_path(db_session: Session, populated_purchase):
    purchase, receipt, auth, clock = populated_purchase
    fulf_service = FulfillmentService(db=db_session, clock=clock)

    # Ingest perfect fulfillment evidence -> Step 8 & Step 9
    fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="carrier",
            external_event_id="EVT-PERFECT",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    )

    # Step 10: Settle capture
    append_event(db_session, purchase.id, "FUNDS_CAPTURED", "agent", {"capture_id": "CAP-001", "amount_cents": 39900}, clock)
    db_session.commit()

    replay_service = ReplayService(db=db_session)
    data = replay_service.get_replay_timeline(purchase.id)

    assert len(data.steps) == 10
    assert data.steps[0].name == "Buyer Instruction"
    assert data.steps[0].status == "COMPLETED"
    assert data.steps[1].name == "Constraints Extracted"
    assert data.steps[1].status == "COMPLETED"
    assert data.steps[4].name == "Receipt Compiled & Hashed"
    assert data.steps[5].name == "Buyer Approved Receipt"
    assert data.steps[6].name == "PayPal Hold Authorized"
    assert data.steps[7].name == "Fulfillment Ingestion"
    assert data.steps[7].status == "COMPLETED"
    assert data.steps[8].name == "Gate Decision"
    assert data.steps[8].status == "COMPLETED"
    assert data.steps[8].is_divergence is False
    assert data.steps[9].name == "Settlement Capture"
    assert data.steps[9].status == "COMPLETED"

    # Integrity verification
    assert data.chain_intact is True
    assert data.broken_step is None
    assert data.chain_event_count > 0
    assert data.is_diverged is False
    assert data.divergence_step is None


def test_replay_divergence_highlighted_on_drift(db_session: Session, populated_purchase):
    purchase, receipt, auth, clock = populated_purchase
    fulf_service = FulfillmentService(db=db_session, clock=clock)

    # Ingest refurbished evidence -> triggers DRIFT
    fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="carrier",
            external_event_id="EVT-REFURB",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-REFURB",
            condition="REFURBISHED",
            color="black",
        )
    )

    replay_service = ReplayService(db=db_session)
    data = replay_service.get_replay_timeline(purchase.id)

    assert data.is_diverged is True
    assert data.divergence_step == 9
    assert data.steps[8].name == "Gate Decision"
    assert data.steps[8].status == "DIVERGED"
    assert data.steps[8].is_divergence is True
    assert "Refurbished" in data.steps[8].details or "deviates" in data.steps[8].details

    # Step 10 should be BLOCKED
    assert data.steps[9].status == "BLOCKED"
    assert data.chain_intact is True


def test_replay_detects_tampering_in_ledger_chain(db_session: Session, populated_purchase):
    purchase, receipt, auth, clock = populated_purchase

    # Tamper with event #3 payload in database
    event_3 = db_session.query(DecisionEvent).filter_by(purchase_id=purchase.id, seq=3).first()
    assert event_3 is not None
    event_3.payload = '{"tampered": true}'
    db_session.commit()

    replay_service = ReplayService(db=db_session)
    data = replay_service.get_replay_timeline(purchase.id)

    assert data.chain_intact is False
    assert data.broken_step == 3
