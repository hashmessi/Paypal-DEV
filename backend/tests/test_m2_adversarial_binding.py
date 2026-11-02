"""Adversarial stress test suite for M2: custom_id hash binding and gateway simulation matrix."""

import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.payments.fake import FakeGateway
from app.proof.counterfactual import gateway_is_simulated


def test_adversarial_prefixed_receipt_hash_binding(client: TestClient, fake_gateway: FakeGateway):
    """Verify that a 71-char sha256: prefixed receipt hash is bound to custom_id without truncation."""
    raw_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    prefixed_hash = f"sha256:{raw_hash}"
    assert len(prefixed_hash) == 71

    resp = client.post(
        "/checkout/orders",
        json={
            "ref": "ORD-BOUND-PREFIX-001",
            "amount_cents": 4999,
            "currency": "USD",
            "receipt_hash": prefixed_hash,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    order_id = data["order_id"]

    gw_order = fake_gateway.orders.get(order_id)
    assert gw_order is not None
    assert gw_order.get("custom_id") == prefixed_hash
    assert len(gw_order.get("custom_id")) == 71
    # Verify exact roundtrip without truncation
    assert gw_order.get("custom_id")[7:] == raw_hash


@pytest.mark.parametrize(
    "raw_cid,expected_simulated",
    [
        ("test", True),
        ("sandbox_test", True),
        ("", True),
        ("   ", True),
        ("  test  ", True),
        ("  sandbox_test  ", True),
        (None, True),
        ("A21AAY-RealSandboxCredential-987", False),
        ("live_client_id_paypal_12345", False),
    ],
)
def test_adversarial_client_id_simulation_matrix(monkeypatch, raw_cid, expected_simulated):
    """Stress-test gateway_is_simulated against all client ID variations."""
    monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", raw_cid)
    assert gateway_is_simulated() == expected_simulated
