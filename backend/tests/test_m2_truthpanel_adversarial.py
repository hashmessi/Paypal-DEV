"""Adversarial stress tests for Milestone M2 TruthPanel backend contracts."""

import pytest
from fastapi.testclient import TestClient


from app.core.config import settings


def test_truthpanel_backend_contract_matrix(client: TestClient, monkeypatch):
    """Assert payment payload exposes real runtime simulation flag and correct null states."""
    # 1. Test simulated mode (default credentials)
    monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "test")
    resp = client.post(
        "/checkout/orders",
        json={"ref": "ORD-M2-ADV-001", "amount_cents": 7999, "currency": "USD"},
    )
    assert resp.status_code == 201
    purchase_id = resp.json()["purchase_id"]

    # Initial state (created, not yet authorized)
    p_resp = client.get(f"/promises/{purchase_id}")
    assert p_resp.status_code == 200
    data = p_resp.json()
    payment = data["payment"]

    assert payment["is_simulated"] is True
    assert payment["order_id"].startswith("ORDER-")
    assert payment["authorization_id"] is None
    assert payment["capture_id"] is None
    assert payment["state"] == "created"
    assert payment["amount_cents"] == 7999
    assert payment["currency"] == "USD"
    assert payment["voided_at"] is None
    assert payment["void_reason"] is None

    # Assert no leaked mock strings
    raw_text = p_resp.text
    assert "3KX8291048194" not in raw_text
    assert "9K3184920194" not in raw_text

    # 2. Authorize
    client.post(f"/checkout/orders/{payment['order_id']}/authorize")
    p_auth = client.get(f"/promises/{purchase_id}").json()["payment"]
    assert p_auth["state"] == "authorized"
    assert p_auth["authorization_id"] is not None
    assert p_auth["authorization_id"].startswith("AUTH-")
    assert p_auth["capture_id"] is None

    # 3. Void with explicit reason and verify metadata
    void_reason = "Drift gate test rejection: unauthorized item substitution"
    v_resp = client.post(
        f"/purchases/{purchase_id}/void",
        json={"reason": void_reason},
    )
    assert v_resp.status_code == 200
    assert v_resp.json()["status"] == "VOIDED"

    p_void = client.get(f"/promises/{purchase_id}").json()["payment"]
    assert p_void["state"] == "voided"
    assert p_void["void_reason"] == void_reason
    assert p_void["voided_at"] is not None
    assert "T" in p_void["voided_at"]  # valid ISO string


def test_truthpanel_live_credentials_flag(client: TestClient, monkeypatch):
    """When credentials are live sandbox, is_simulated evaluates to False."""
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "AV-Live-Sandbox-Client-Id-999")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "Live-Secret-999")

    resp = client.post(
        "/checkout/orders",
        json={"ref": "ORD-M2-LIVE-001", "amount_cents": 12500, "currency": "USD"},
    )
    assert resp.status_code == 201
    purchase_id = resp.json()["purchase_id"]

    p_resp = client.get(f"/promises/{purchase_id}")
    assert p_resp.status_code == 200
    payment = p_resp.json()["payment"]
    assert payment["is_simulated"] is False
