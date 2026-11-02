"""Test post-capture shipment tracking push to PayPal Orders v2."""

from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.clock import FixedClock
from app.core.models import Base, DecisionEvent
from app.drift.models import GateOutcome
from app.fulfillment.models import IngestEvidenceRequest
from app.fulfillment.service import FulfillmentService
from app.payments.fake import FakeGateway
from app.payments.service import PaymentsService
from tests.test_acceptance_cases import create_test_purchase


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


@pytest.mark.asyncio
async def test_capture_pushes_tracking_to_gateway_and_ledger(db_session: Session):
    clock = FixedClock(datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc))
    purchase, receipt, auth = create_test_purchase(db_session, clock)
    gateway = FakeGateway()
    gw_order = await gateway.create_order(amount_cents=auth.amount_cents, currency=auth.currency, ref=purchase.ref)
    gw_auth = await gateway.authorize_order(gw_order["order_id"])
    auth.authorization_id = gw_auth["authorization_id"]
    auth.order_id = gw_order["order_id"]
    db_session.commit()

    fulf_service = FulfillmentService(db=db_session, clock=clock)
    payments_service = PaymentsService(session=db_session, gateway=gateway, clock=clock)

    # Ingest carrier accepted evidence matching the contract -> MATCH
    res = fulf_service.ingest_evidence(
        IngestEvidenceRequest(
            purchase_id=purchase.id,
            source="UPS",
            external_event_id="1Z9999999999999999",
            trust_level="CARRIER_TELEMETRY",
            carrier_status="ACCEPTED",
            sku="WH1000XM5-BLK-NEW",
            condition="NEW",
            color="black",
            eta=clock.now() + timedelta(days=2),
        )
    )
    assert res.gate.outcome == GateOutcome.MATCH

    # Capture authorization
    cap_res = await payments_service.capture_authorization(purchase_id=purchase.id)
    assert cap_res["status"] == "COMPLETED"

    # Assert tracking was pushed to gateway
    assert len(gateway.tracking_records) == 1
    tr = gateway.tracking_records[0]
    assert tr["order_id"] == auth.order_id
    assert tr["carrier"] == "UPS"
    assert tr["tracking_number"] == "1Z9999999999999999"
    assert tr["sku"] == "WH1000XM5-BLK-NEW"

    # Assert TRACKING_PUSHED_TO_PAYPAL event in ledger
    events = (
        db_session.query(DecisionEvent)
        .filter(DecisionEvent.purchase_id == purchase.id, DecisionEvent.event_type == "TRACKING_PUSHED_TO_PAYPAL")
        .all()
    )
    import json
    assert len(events) == 1
    ev_payload = json.loads(events[0].payload) if isinstance(events[0].payload, str) else events[0].payload
    assert ev_payload["carrier"] == "UPS"
    assert ev_payload["tracking_number"] == "1Z9999999999999999"
    assert ev_payload["sku"] == "WH1000XM5-BLK-NEW"
