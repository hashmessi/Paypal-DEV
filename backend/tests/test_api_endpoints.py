"""Integration tests for FastAPI endpoints with TestClient."""

import json
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_checkout_and_capture_flow(client: TestClient, bind_receipt):
    """Full lifecycle: create order -> authorize -> capture -> verify ledger."""
    # 1. Create order
    order_payload = {
        "ref": "ORD-E2E-001",
        "amount_cents": 8999,
        "currency": "USD",
        "buyer_instruction": "Deliver Sony WH-1000XM5 Black Brand New",
    }
    resp = client.post("/checkout/orders", json=order_payload)
    assert resp.status_code == 201
    order_data = resp.json()
    purchase_id = order_data["purchase_id"]
    order_id = order_data["order_id"]
    bind_receipt(purchase_id, 8999)
    assert order_id.startswith("ORDER-")
    assert "approval_url" in order_data

    # 2. Authorize order
    auth_resp = client.post(f"/checkout/orders/{order_id}/authorize")
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    assert auth_data["state"] == "authorized"
    assert auth_data["authorization_id"].startswith("AUTH-")

    # 3. Capture purchase
    cap_resp = client.post(
        f"/purchases/{purchase_id}/capture",
        json={"note": "Autonomous delivery verified"},
    )
    assert cap_resp.status_code == 200
    cap_data = cap_resp.json()
    assert cap_data["status"] == "COMPLETED"
    assert cap_data["capture_id"].startswith("CAP-")

    # 4. Duplicate capture (idempotency check)
    dup_cap_resp = client.post(
        f"/purchases/{purchase_id}/capture",
        json={"note": "Duplicate call"},
    )
    assert dup_cap_resp.status_code == 200
    assert dup_cap_resp.json()["capture_id"] == cap_data["capture_id"]

    # 5. Void on captured purchase must fail with 409 Conflict (PAY-04 terminal state)
    void_resp = client.post(
        f"/purchases/{purchase_id}/void",
        json={"reason": "Late cancel attempt"},
    )
    assert void_resp.status_code == 409

    # 6. Replay ledger audit trail
    replay_resp = client.get(f"/purchases/{purchase_id}/replay")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert replay_data["events_count"] >= 3
    event_types = [ev["event_type"] for ev in replay_data["events"]]
    assert "ORDER_CREATED" in event_types
    assert "FUNDS_AUTHORIZED" in event_types
    assert "FUNDS_CAPTURED" in event_types

    # 7. Cryptographic ledger verification
    verify_resp = client.post(f"/purchases/{purchase_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True
    assert verify_resp.json()["broken_seq"] is None


def test_void_lifecycle(client: TestClient):
    """Lifecycle for order creation -> authorize -> buyer void."""
    # Create order
    resp = client.post(
        "/checkout/orders",
        json={"ref": "ORD-VOID-001", "amount_cents": 4500, "currency": "USD"},
    )
    assert resp.status_code == 201
    purchase_id = resp.json()["purchase_id"]
    order_id = resp.json()["order_id"]

    # Authorize
    client.post(f"/checkout/orders/{order_id}/authorize")

    # Void
    void_resp = client.post(
        f"/purchases/{purchase_id}/void",
        json={"reason": "Buyer decided to cancel"},
    )
    assert void_resp.status_code == 200
    assert void_resp.json()["status"] == "VOIDED"

    # Capture on voided purchase must fail with 409
    cap_resp = client.post(f"/purchases/{purchase_id}/capture")
    assert cap_resp.status_code == 409


def test_demo_scenarios_and_tamper_detection(client: TestClient, monkeypatch):
    """Verify demo scenario seeding and cryptographic tamper detection."""
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "t0ken")
    # Seed tampered scenario
    tamp_resp = client.post(
        "/demo/scenarios",
        json={"scenario": "tampered_ledger", "amount_cents": 12000},
        headers={"X-Admin-Token": "t0ken"},
    )
    assert tamp_resp.status_code == 200
    tamp_purchase_id = tamp_resp.json()["purchase_id"]

    # Verify that ledger audit detects tampering
    verify_resp = client.post(f"/purchases/{tamp_purchase_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is False
    assert verify_resp.json()["broken_seq"] is not None


def test_webhook_endpoint_flow(client: TestClient):
    """Verify webhook endpoint ingestion with raw body headers."""
    wh_headers = {
        "paypal-auth-algo": "SHA256withRSA",
        "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-123",
        "paypal-transmission-id": "trans-api-123",
        "paypal-transmission-sig": "test-sig",
        "paypal-transmission-time": "2026-11-01T12:00:00Z",
    }
    payload = {
        "id": "WH-API-TEST-001",
        "event_type": "PAYMENT.AUTHORIZATION.VOIDED",
        "resource": {"id": "AUTH-API-TEST"},
    }

    resp = client.post(
        "/webhooks/paypal",
        content=json.dumps(payload),
        headers=wh_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"

    # Duplicate call
    dup_resp = client.post(
        "/webhooks/paypal",
        content=json.dumps(payload),
        headers=wh_headers,
    )
    assert dup_resp.status_code == 200
    assert dup_resp.json()["status"] == "duplicate"
