"""Tests for Fulfillment Evidence Ingestion and Scenario Console (FULF-01, FULF-02, DRIFT-02)."""

from datetime import datetime, timedelta, timezone
import json
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import FixedClock
from app.core.models import (
    Base,
    DecisionEvent,
    FulfillmentEvidence,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.fulfillment.models import IngestEvidenceRequest
from app.fulfillment.scenarios import ScenarioRunner
from app.fulfillment.service import FulfillmentService
from app.ledger.verify import verify_chain


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
def setup_purchase(db_session: Session):
    clock = FixedClock(datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc))
    purchase = Purchase(
        ref="PUR-TEST-FULF",
        buyer_instruction="Buy Sony WH-1000XM5 under $400 new in black",
        status="authorized",
    )
    db_session.add(purchase)
    db_session.flush()

    conditions = {
        "expected_sku": "WH1000XM5-BLK-NEW",
        "expected_color": "black",
        "reject_refurbished": True,
        "max_delivery_days": 5,
    }
    receipt = PromiseReceipt(
        purchase_id=purchase.id,
        version=1,
        receipt_hash="a" * 64,
        status="active",
        canonical_payload="{}",
        constraints_json=json.dumps({"max_budget_cents": 40000, "allow_refurbished": False}),
        product_snapshot_json=json.dumps({"title": "Sony WH-1000XM5", "sku": "WH1000XM5-BLK-NEW", "color": "black"}),
        merchant_quote_json=json.dumps({"item_cents": 39900, "shipping_cents": 0, "tax_cents": 0, "total_cents": 39900, "currency": "USD"}),
        total_cents=39900,
        currency="USD",
        capture_conditions_json=json.dumps(conditions),
        created_at=clock.now(),
    )
    db_session.add(receipt)

    auth = PaymentAuthorization(
        purchase_id=purchase.id,
        authorization_id="AUTH-FULF-01",
        order_id="ORDER-FULF-01",
        state="authorized",
        amount_cents=39900,
        currency="USD",
        expiration_time=clock.now() + timedelta(days=29),
        created_at=clock.now(),
    )
    db_session.add(auth)
    db_session.commit()
    return purchase, receipt, auth, clock


def test_evidence_ingestion_and_ledger_recording(db_session: Session, setup_purchase):
    purchase, receipt, auth, clock = setup_purchase
    service = FulfillmentService(db=db_session, clock=clock)

    req = IngestEvidenceRequest(
        purchase_id=purchase.id,
        source="carrier",
        external_event_id="EVT-INGEST-01",
        trust_level="CARRIER_TELEMETRY",
        is_synthetic=False,
        carrier_status="ACCEPTED",
        sku="WH1000XM5-BLK-NEW",
        condition="NEW",
        color="black",
        eta=clock.now() + timedelta(days=2),
    )
    res = service.ingest_evidence(req)
    assert res.status == "ingested"
    assert res.evidence_id is not None
    assert res.gate is not None
    assert res.gate.outcome.value == "MATCH"
    assert res.gate.status_pill == "AUTHORIZED · NOT CAPTURED"

    # Verify database persistence
    evidence = service.get_evidence_list(purchase.id)
    assert len(evidence) == 1
    assert evidence[0].external_event_id == "EVT-INGEST-01"
    assert evidence[0].carrier_status == "ACCEPTED"

    # Verify decision ledger events
    stmt = (
        select(DecisionEvent)
        .where(DecisionEvent.purchase_id == purchase.id)
        .order_by(DecisionEvent.seq.asc())
    )
    events = list(db_session.execute(stmt).scalars().all())
    event_types = [e.event_type for e in events]
    assert "EVIDENCE_INGESTED" in event_types
    assert "GATE_EVALUATED" in event_types

    # Verify cryptographic ledger chain integrity
    is_valid, count, broken_seq = verify_chain(db_session, purchase.id)
    assert is_valid is True
    assert count == len(events)
    assert broken_seq is None


def test_evidence_deduplication(db_session: Session, setup_purchase):
    purchase, receipt, auth, clock = setup_purchase
    service = FulfillmentService(db=db_session, clock=clock)

    req = IngestEvidenceRequest(
        purchase_id=purchase.id,
        source="carrier",
        external_event_id="EVT-DEDUP-01",
        trust_level="CARRIER_TELEMETRY",
        is_synthetic=False,
        carrier_status="ACCEPTED",
        sku="WH1000XM5-BLK-NEW",
        condition="NEW",
        color="black",
    )
    # First delivery
    res1 = service.ingest_evidence(req)
    assert res1.status == "ingested"

    # Duplicate delivery with exact same (purchase_id, source, external_event_id)
    res2 = service.ingest_evidence(req)
    assert res2.status == "duplicate"
    assert res2.evidence_id == res1.evidence_id

    # Verify evidence count is still 1
    evidence = service.get_evidence_list(purchase.id)
    assert len(evidence) == 1


def test_scenario_console_runner_triggers(db_session: Session, setup_purchase):
    purchase, receipt, auth, clock = setup_purchase
    runner = ScenarioRunner(db=db_session, clock=clock)

    # 1. Trigger Refurbished -> DRIFT (CAPTURE BLOCKED)
    res_refurb = runner.trigger_scenario(purchase.id, "refurbished")
    assert res_refurb["gate_outcome"] == "DRIFT"
    assert res_refurb["status_pill"] == "CAPTURE BLOCKED"
    assert purchase.status == "capture_blocked"

    # 2. Trigger Wrong Color -> DRIFT (CAPTURE BLOCKED)
    res_color = runner.trigger_scenario(purchase.id, "wrong_color")
    assert res_color["gate_outcome"] == "DRIFT"
    assert res_color["status_pill"] == "CAPTURE BLOCKED"

    # 3. Trigger Seller Corrected -> MATCH (AUTHORIZED · NOT CAPTURED)
    res_correct = runner.trigger_scenario(purchase.id, "corrected")
    assert res_correct["gate_outcome"] == "MATCH"
    assert res_correct["status_pill"] == "AUTHORIZED · NOT CAPTURED"
    assert purchase.status == "authorized"

    # 4. Trigger Label Only -> HOLD (HOLD)
    # Clear prior evidence to test isolated label_only
    db_session.query(FulfillmentEvidence).filter_by(purchase_id=purchase.id).delete()
    db_session.commit()
    res_label = runner.trigger_scenario(purchase.id, "label_only")
    assert res_label["gate_outcome"] == "HOLD"
    assert res_label["status_pill"] == "HOLD"

    # 5. Trigger Late ETA -> HOLD (HOLD)
    res_late = runner.trigger_scenario(purchase.id, "late_eta")
    assert res_late["gate_outcome"] == "HOLD"
    assert res_late["status_pill"] == "HOLD"

    # 6. Trigger Duplicate Event -> duplicate
    res_dup = runner.trigger_scenario(purchase.id, "duplicate_event")
    assert res_dup["status"] == "duplicate"

    # 7. Trigger Advance Clock past auth expiry -> PROHIBITED (RENEWAL_REQUIRED)
    res_clock = runner.trigger_scenario(purchase.id, "advance_clock")
    assert res_clock["gate_outcome"] == "PROHIBITED"
    assert res_clock["status_pill"] == "RENEWAL_REQUIRED"
    assert purchase.status == "renewal_required"
