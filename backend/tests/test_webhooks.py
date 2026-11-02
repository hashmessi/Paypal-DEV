"""Tests for PayPal Webhooks signature verification and deduplication (PAY-06)."""

import json
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import FixedClock
from app.core.models import PaymentAuthorization, Purchase, WebhookEvent
from app.payments.fake import FakeGateway
from app.payments.state import PaymentState
from app.webhooks.processor import WebhookProcessor
from app.webhooks.verify import verify_webhook_signature


@pytest.fixture
def sample_webhook_headers() -> dict[str, str]:
    return {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-123",
        "paypal-transmission-id": "trans-12345",
        "paypal-transmission-sig": "signature-bytes-base64",
        "paypal-transmission-time": "2026-11-01T12:00:00Z",
    }


@pytest.fixture
def sample_webhook_payload() -> dict:
    return {
        "id": "WH-999-DEDUP",
        "event_type": "PAYMENT.AUTHORIZATION.VOIDED",
        "create_time": "2026-11-01T12:00:00Z",
        "resource_type": "authorization",
        "resource": {
            "id": "AUTH-SAMPLE-WH",
            "status": "VOIDED",
            "amount": {"currency_code": "USD", "value": "89.99"},
        },
    }


@pytest.mark.asyncio
async def test_webhook_signature_verification(fake_gateway: FakeGateway, sample_webhook_headers: dict):
    """Verify raw body signature check against gateway."""
    raw_body = '{"id":"WH-1","event_type":"TEST"}'

    # Success case
    fake_gateway.webhook_verify_result = True
    assert await verify_webhook_signature(sample_webhook_headers, raw_body, fake_gateway, "wh-id") is True

    # Failure case
    fake_gateway.webhook_verify_result = False
    assert await verify_webhook_signature(sample_webhook_headers, raw_body, fake_gateway, "wh-id") is False

    # Missing header case
    broken_headers = sample_webhook_headers.copy()
    del broken_headers["paypal-transmission-sig"]
    assert await verify_webhook_signature(broken_headers, raw_body, fake_gateway, "wh-id") is False


@pytest.mark.asyncio
async def test_webhook_deduplication(
    db_session: Session, fixed_clock: FixedClock, sample_webhook_headers: dict, sample_webhook_payload: dict
):
    """Ensure duplicate webhook events return duplicate status and do not duplicate records."""
    processor = WebhookProcessor(session=db_session, clock=fixed_clock)
    raw_body = json.dumps(sample_webhook_payload)

    # First delivery
    res1 = await processor.process_event(sample_webhook_headers, raw_body, verified=True)
    assert res1["status"] == "processed"
    assert res1["event_id"] == "WH-999-DEDUP"

    # Second delivery (identical event_id)
    res2 = await processor.process_event(sample_webhook_headers, raw_body, verified=True)
    assert res2["status"] == "duplicate"
    assert res2["event_id"] == "WH-999-DEDUP"

    # Only one record in database
    events = db_session.execute(select(WebhookEvent)).scalars().all()
    assert len(events) == 1


@pytest.mark.asyncio
async def test_webhook_never_triggers_automatic_capture(
    db_session: Session, fixed_clock: FixedClock, sample_webhook_headers: dict
):
    """PAY-06: Invariant — Webhook event reception must NEVER trigger an automatic capture."""
    p = Purchase(ref="PURCH-WH-01", buyer_instruction="Webhook test", status="draft")
    db_session.add(p)
    db_session.flush()

    auth = PaymentAuthorization(
        purchase_id=p.id,
        authorization_id="AUTH-NO-CAPTURE",
        order_id="ORD-NO-CAPTURE",
        state=PaymentState.AUTHORIZED.value,
        amount_cents=8999,
        currency="USD",
    )
    db_session.add(auth)
    db_session.commit()

    processor = WebhookProcessor(session=db_session, clock=fixed_clock)
    wh_payload = {
        "id": "WH-CHECK-INVARIANT",
        "event_type": "PAYMENT.AUTHORIZATION.CREATED",
        "resource": {"id": "AUTH-NO-CAPTURE"},
    }
    await processor.process_event(sample_webhook_headers, json.dumps(wh_payload), verified=True)

    # State must still be authorized, NOT captured
    db_session.refresh(auth)
    assert auth.state == PaymentState.AUTHORIZED.value
    assert auth.capture_id is None

