"""Tests verifying PaymentGateway protocol contracts for both Fake and PayPal adapters."""

import pytest

from app.core.config import settings
from app.api.deps import get_gateway, _fake_gateway_singleton
from app.payments.fake import FakeGateway
from app.payments.port import PaymentGateway
from app.payments.paypal import PayPalGateway
from app.proof.counterfactual import gateway_is_simulated


def test_gateway_protocol_conformance():
    """Verify runtime checkable protocol compliance."""
    fake = FakeGateway()
    paypal = PayPalGateway(client_id="dummy", client_secret="dummy")

    assert isinstance(fake, PaymentGateway)
    assert isinstance(paypal, PaymentGateway)
    assert hasattr(fake, "push_tracking")
    assert hasattr(paypal, "push_tracking")


@pytest.mark.asyncio
async def test_fake_gateway_push_tracking():
    """Verify push_tracking record storage on FakeGateway."""
    gw = FakeGateway()
    res = await gw.push_tracking(
        order_id="ORD-123",
        capture_id="CAP-456",
        carrier="UPS",
        tracking_number="1Z9999999999999999",
        sku="WH1000XM5-BLK-NEW",
    )
    assert res["status"] == "TRACKING_RECORDED"
    assert res["order_id"] == "ORD-123"
    assert res["capture_id"] == "CAP-456"
    assert res["carrier"] == "UPS"
    assert res["tracking_number"] == "1Z9999999999999999"
    assert res["sku"] == "WH1000XM5-BLK-NEW"
    assert len(gw.tracking_records) == 1
    assert gw.tracking_records[0] == res


@pytest.mark.parametrize(
    "client_id,demo_mode,expected_simulated",
    [
        ("", True, True),
        ("", False, True),
        ("   ", True, True),
        ("   ", False, True),
        (None, True, True),
        (None, False, True),
        ("test", True, True),
        ("test", False, True),
        ("sandbox_test", True, True),
        ("sandbox_test", False, True),
        ("AX_live_sandbox_client_id_123", True, False),
        ("AX_live_sandbox_client_id_123", False, False),
    ],
)
def test_gateway_is_simulated_and_deps_matrix(monkeypatch, client_id, demo_mode, expected_simulated):
    """Test that gateway_is_simulated decouples from DEMO_MODE and checks credentials strictly."""
    monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", client_id)
    monkeypatch.setattr(settings, "DEMO_MODE", demo_mode)

    simulated = gateway_is_simulated()
    assert simulated is expected_simulated

    gw = get_gateway()
    if expected_simulated:
        assert gw is _fake_gateway_singleton
        assert isinstance(gw, FakeGateway)
    else:
        assert isinstance(gw, PayPalGateway)
        assert gw is not _fake_gateway_singleton


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

