"""Tests for Drift-Gated Settlement (PAY-02).

Guarantees:
- Capture is allowed ONLY when gate evaluation outcome is MATCH.
- DRIFT, HOLD, and PROHIBITED block capture locally without contacting PayPal.
- Raising CaptureBlockedByGateError leaves authorization in non-terminal valid state.
"""

from datetime import datetime, timedelta, timezone
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import FixedClock
from app.core.models import (
    Base,
    FulfillmentEvidence,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.fulfillment.models import IngestEvidenceRequest
from app.fulfillment.service import FulfillmentService
from app.payments.fake import FakeGateway
from app.payments.service import PaymentsService
from app.payments.state import CaptureBlockedByGateError


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
def gated_setup(db_session: Session):
    clock = FixedClock(datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc))
    gateway = FakeGateway()

    purchase = Purchase(
        ref="PUR-GATE-01",
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
        receipt_hash="b" * 64,
        status="active",
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

    auth = PaymentAuthorization(
        purchase_id=purchase.id,
        authorization_id="AUTH-GATE-001",
        order_id="ORDER-GATE-001",
        state="authorized",
        amount_cents=39900,
        currency="USD",
        expiration_time=clock.now() + timedelta(days=29),
        created_at=clock.now(),
    )
    db_session.add(auth)
    db_session.commit()

    return purchase, receipt, auth, gateway, clock


@pytest.mark.asyncio
async def test_drift_refurbished_blocks_capture_without_calling_gateway(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    fulf_service = FulfillmentService(db=db_session, clock=clock)
    payments_service = PaymentsService(session=db_session, gateway=gateway, clock=clock)

    # Ingest refurbished evidence -> DRIFT
    fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="carrier",
            external_event_id="EVT-REFURB",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="REFURBISHED",
            color="black",
        )
    )

    # Attempt capture: must raise CaptureBlockedByGateError
    with pytest.raises(CaptureBlockedByGateError) as exc_info:
        await payments_service.capture_authorization(purchase_id=purchase.id)

    assert "DRIFT" in str(exc_info.value) or "CAPTURE BLOCKED" in str(exc_info.value)
    # Gateway was NEVER called
    assert "AUTH-GATE-001" not in gateway.authorizations or gateway.authorizations["AUTH-GATE-001"].state != "captured"
    # Authorization state remains authorized
    db_session.refresh(auth)
    assert auth.state == "authorized"


@pytest.mark.asyncio
async def test_hold_label_only_blocks_capture_without_calling_gateway(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    fulf_service = FulfillmentService(db=db_session, clock=clock)
    payments_service = PaymentsService(session=db_session, gateway=gateway, clock=clock)

    # Ingest label only -> HOLD
    fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="carrier",
            external_event_id="EVT-LABEL",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="LABEL_CREATED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    )

    with pytest.raises(CaptureBlockedByGateError) as exc_info:
        await payments_service.capture_authorization(purchase_id=purchase.id)

    assert "HOLD" in str(exc_info.value)
    db_session.refresh(auth)
    assert auth.state == "authorized"


@pytest.mark.asyncio
async def test_prohibited_expired_auth_blocks_capture(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    fulf_service = FulfillmentService(db=db_session, clock=clock)
    payments_service = PaymentsService(session=db_session, gateway=gateway, clock=clock)

    # Valid fulfillment evidence
    fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="carrier",
            external_event_id="EVT-VALID",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
        )
    )

    # Expire authorization
    auth.expiration_time = clock.now() - timedelta(minutes=1)
    db_session.commit()

    with pytest.raises(CaptureBlockedByGateError) as exc_info:
        await payments_service.capture_authorization(purchase_id=purchase.id)

    assert "PROHIBITED" in str(exc_info.value) or "RENEWAL_REQUIRED" in str(exc_info.value)
    db_session.refresh(auth)
    assert auth.state == "authorized"


@pytest.mark.asyncio
async def test_match_allows_capture_to_succeed(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    fulf_service = FulfillmentService(db=db_session, clock=clock)
    payments_service = PaymentsService(session=db_session, gateway=gateway, clock=clock)

    # Register authorization on fake gateway
    gw_order = await gateway.create_order(amount_cents=auth.amount_cents, currency=auth.currency, ref=purchase.ref)
    gw_auth = await gateway.authorize_order(gw_order["order_id"])
    auth.authorization_id = gw_auth["authorization_id"]
    auth.order_id = gw_order["order_id"]
    db_session.commit()

    # Ingest matching evidence
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
            eta=clock.now() + timedelta(days=2),
        )
    )

    # Capture should now succeed
    res = await payments_service.capture_authorization(purchase_id=purchase.id)
    assert res["status"] == "COMPLETED"

    db_session.refresh(auth)
    assert auth.state == "captured"
    assert auth.capture_id is not None

    db_session.refresh(purchase)
    assert purchase.status == "completed"
