"""Tests verifying PaymentGateway protocol contracts for both Fake and PayPal adapters."""

import pytest

from app.payments.fake import FakeGateway
from app.payments.port import PaymentGateway
from app.payments.paypal import PayPalGateway


def test_gateway_protocol_conformance():
    """Verify runtime checkable protocol compliance."""
    fake = FakeGateway()
    paypal = PayPalGateway(client_id="dummy", client_secret="dummy")

    assert isinstance(fake, PaymentGateway)
    assert isinstance(paypal, PaymentGateway)


@pytest.mark.asyncio
async def test_fake_gateway_lifecycle():
    """Verify standard lifecycle operations on FakeGateway."""
    gw = FakeGateway()

    # 1. Create order
    order = await gw.create_order(
        amount_cents=8999,
        currency="USD",
        ref="REF-001",
    )
    assert order["status"] == "CREATED"
    assert "order_id" in order
    assert order["amount_cents"] == 8999
    assert "approval_url" in order

    # 2. Authorize order
    auth = await gw.authorize_order(order["order_id"])
    assert auth["status"] == "CREATED"
    assert "authorization_id" in auth
    assert auth["amount_cents"] == 8999

    # 3. Reconcile authorization
    recon = await gw.reconcile_authorization(auth["authorization_id"])
    assert recon["status"] == "CREATED"
    assert recon["authorization_id"] == auth["authorization_id"]

    # 4. Capture authorization
    cap = await gw.capture_authorization(
        authorization_id=auth["authorization_id"],
        amount_cents=8999,
        currency="USD",
        request_id="req-cap-1",
    )
    assert cap["status"] == "COMPLETED"
    assert "capture_id" in cap

    # Reconcile after capture
    recon_after = await gw.reconcile_authorization(auth["authorization_id"])
    assert recon_after["status"] == "CAPTURED"


@pytest.mark.asyncio
async def test_fake_gateway_void_lifecycle():
    """Verify void flow on FakeGateway."""
    gw = FakeGateway()
    order = await gw.create_order(amount_cents=2500, currency="USD", ref="REF-002")
    auth = await gw.authorize_order(order["order_id"])

    void_res = await gw.void_authorization(
        authorization_id=auth["authorization_id"],
        request_id="req-void-1",
    )
    assert void_res["status"] == "VOIDED"

    recon = await gw.reconcile_authorization(auth["authorization_id"])
    assert recon["status"] == "VOIDED"

