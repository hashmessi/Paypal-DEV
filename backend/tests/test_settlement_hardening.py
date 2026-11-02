"""Regression tests for settlement hardening: fail-closed capture, amount binding, authorize status check."""

import json

import pytest
from sqlalchemy.orm import Session

from app.core.models import PaymentAuthorization, Purchase
from app.payments.fake import FakeGateway
from app.payments.service import PaymentsService
from app.payments.state import CaptureBlockedByGateError, PaymentStateError
from app.webhooks.processor import WebhookProcessor
from tests.test_gated_settlement import db_session, gated_setup  # noqa: F401  shared fixtures


class PendingAuthGateway(FakeGateway):
    """Gateway whose authorize returns PayPal PENDING: funds are not held."""

    async def authorize_order(self, order_id: str):
        res = await super().authorize_order(order_id)
        res["status"] = "PENDING"
        return res


@pytest.mark.asyncio
async def test_capture_fails_closed_without_receipt(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    db_session.delete(receipt)
    db_session.commit()

    service = PaymentsService(session=db_session, gateway=gateway, clock=clock)
    with pytest.raises(CaptureBlockedByGateError, match="no Promise Receipt"):
        await service.capture_authorization(purchase_id=purchase.id)

    db_session.refresh(auth)
    assert auth.state == "authorized"
    assert auth.capture_id is None


@pytest.mark.asyncio
async def test_authorized_amount_must_match_receipt_total(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    auth.amount_cents = 100  # buyer order under-funded vs approved 39900
    db_session.commit()

    service = PaymentsService(session=db_session, gateway=gateway, clock=clock)
    with pytest.raises(CaptureBlockedByGateError) as exc:
        await service.capture_authorization(purchase_id=purchase.id)

    assert exc.value.outcome == "DRIFT"
    assert any(f["invariant_code"] == "INV-07-AMOUNT" for f in exc.value.findings)


@pytest.mark.asyncio
async def test_capture_amount_cannot_exceed_authorized_amount(db_session: Session, gated_setup):
    purchase, receipt, auth, gateway, clock = gated_setup
    gw_order = await gateway.create_order(amount_cents=auth.amount_cents, currency=auth.currency, ref=purchase.ref)
    gw_auth = await gateway.authorize_order(gw_order["order_id"])
    auth.authorization_id = gw_auth["authorization_id"]
    auth.order_id = gw_order["order_id"]
    db_session.commit()

    service = PaymentsService(session=db_session, gateway=gateway, clock=clock)
    with pytest.raises(ValueError, match="exceeds authorized amount"):
        await service.capture_authorization(purchase_id=purchase.id, amount_cents=auth.amount_cents + 1)

    db_session.refresh(auth)
    assert auth.state == "authorized"


@pytest.mark.asyncio
async def test_void_webhook_cannot_rewrite_captured_state(db_session: Session, fixed_clock):
    purchase = Purchase(ref="PUR-WH-01", buyer_instruction="webhook terminal guard", status="completed")
    db_session.add(purchase)
    db_session.flush()
    auth = PaymentAuthorization(
        purchase_id=purchase.id,
        authorization_id="AUTH-WH-01",
        order_id="ORDER-WH-01",
        state="captured",
        amount_cents=100,
        currency="USD",
    )
    db_session.add(auth)
    db_session.commit()

    body = json.dumps({"id": "WH-EVT-01", "event_type": "PAYMENT.AUTHORIZATION.VOIDED", "resource": {"id": "AUTH-WH-01"}})
    await WebhookProcessor(session=db_session, clock=fixed_clock).process_event(headers={}, raw_body=body, verified=True)

    db_session.refresh(auth)
    assert auth.state == "captured"
    assert auth.voided_at is None


@pytest.mark.asyncio
async def test_pending_paypal_authorization_is_not_recorded_as_authorized(db_session: Session, gated_setup):
    purchase, receipt, auth, _gateway, clock = gated_setup
    gateway = PendingAuthGateway()
    gw_order = await gateway.create_order(amount_cents=auth.amount_cents, currency=auth.currency, ref=purchase.ref)
    auth.state = "created"
    auth.authorization_id = None
    auth.order_id = gw_order["order_id"]
    db_session.commit()

    service = PaymentsService(session=db_session, gateway=gateway, clock=clock)
    with pytest.raises(PaymentStateError, match="not usable"):
        await service.authorize_order(order_id=gw_order["order_id"])

    db_session.refresh(auth)
    assert auth.state == "created"
    assert auth.authorization_id is None
