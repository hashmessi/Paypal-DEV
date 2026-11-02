"""Tests for Payment Idempotency and Deterministic Headers (PAY-05)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import FixedClock
from app.core.models import FinancialAction, PaymentAuthorization
from app.payments.fake import FakeGateway
from app.payments.service import PaymentsService, generate_deterministic_request_id
from app.payments.state import TerminalStateError


def test_deterministic_request_id_consistency():
    """Verify PayPal-Request-Id is strictly deterministic for same auth and action."""
    auth_id = "AUTH-TEST123456"
    req_id_1 = generate_deterministic_request_id(auth_id, "capture")
    req_id_2 = generate_deterministic_request_id(auth_id, "capture")
    req_id_void = generate_deterministic_request_id(auth_id, "void")

    assert req_id_1 == req_id_2
    assert req_id_1 != req_id_void
    assert len(req_id_1) == 36  # UUID v5 length


@pytest.mark.asyncio
async def test_duplicate_capture_returns_cached_result(
    db_session: Session, fake_gateway: FakeGateway, fixed_clock: FixedClock
):
    """Ensure sending two capture requests returns the identical payload and executes only one gateway capture."""
    service = PaymentsService(session=db_session, gateway=fake_gateway, clock=fixed_clock)

    order = await service.create_checkout_order(
        purchase_ref="ORD-IDEMP-01",
        amount_cents=5000,
        currency="USD",
    )
    purchase_id = order["purchase_id"]
    order_id = order["order_id"]

    await service.authorize_order(order_id=order_id)

    # First capture
    res_1 = await service.capture_authorization(purchase_id=purchase_id, note="First attempt")
    assert res_1["status"] == "COMPLETED"
    capture_id = res_1["capture_id"]

    # Second capture (idempotent duplicate)
    res_2 = await service.capture_authorization(purchase_id=purchase_id, note="Second duplicate attempt")
    assert res_2["capture_id"] == capture_id
    assert res_2["status"] == "COMPLETED"

    # Verify only one capture occurred on fake gateway
    assert len(fake_gateway.captures) == 1

    # Verify only one financial action recorded
    stmt = select(FinancialAction).where(FinancialAction.action == "capture")
    actions = db_session.execute(stmt).scalars().all()
    assert len(actions) == 1
    assert actions[0].status == "completed"


@pytest.mark.asyncio
async def test_duplicate_void_returns_cached_result(
    db_session: Session, fake_gateway: FakeGateway, fixed_clock: FixedClock
):
    """Ensure duplicate void calls return cached result idempotently."""
    service = PaymentsService(session=db_session, gateway=fake_gateway, clock=fixed_clock)

    order = await service.create_checkout_order(
        purchase_ref="ORD-IDEMP-02",
        amount_cents=3500,
        currency="USD",
    )
    purchase_id = order["purchase_id"]
    order_id = order["order_id"]

    await service.authorize_order(order_id=order_id)

    # First void
    res_1 = await service.void_authorization(purchase_id=purchase_id, reason="Cancel 1")
    assert res_1["status"] == "VOIDED"

    # Second void
    res_2 = await service.void_authorization(purchase_id=purchase_id, reason="Cancel 2")
    assert res_2["status"] == "VOIDED"

    assert len(fake_gateway.voids) == 1


def test_financial_actions_unique_constraint(db_session: Session):
    """Verify database unique constraint uq_auth_action rejects duplicate action entries."""
    act1 = FinancialAction(
        authorization_id="AUTH-UNIQUE-TEST",
        action="capture",
        request_id="req-1",
        status="completed",
    )
    db_session.add(act1)
    db_session.commit()

    act2 = FinancialAction(
        authorization_id="AUTH-UNIQUE-TEST",
        action="capture",
        request_id="req-2",
        status="completed",
    )
    db_session.add(act2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

