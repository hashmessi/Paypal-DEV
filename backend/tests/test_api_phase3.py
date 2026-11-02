"""Integration tests for Phase 3 API endpoints (Fulfillment, Gate, Replay, Gated Capture)."""

from datetime import datetime, timezone
import json
import pytest
from fastapi.testclient import TestClient

from app.core.models import PaymentAuthorization, PromiseReceipt, Purchase


def test_fulfillment_evidence_and_gate_api_flow(client: TestClient):
    # 1. Create a purchase and authorization via checkout
    order_payload = {
        "ref": "ORD-P3-001",
        "amount_cents": 39900,
        "currency": "USD",
        "buyer_instruction": "Buy Sony WH-1000XM5 under $400 new in black",
    }
    resp = client.post("/checkout/orders", json=order_payload)
    assert resp.status_code == 201
    purchase_id = resp.json()["purchase_id"]
    order_id = resp.json()["order_id"]

    # Authorize order
    auth_resp = client.post(f"/checkout/orders/{order_id}/authorize")
    assert auth_resp.status_code == 200

    # 2. Compile and approve receipt
    receipt_payload = {
        "purchase_id": purchase_id,
        "constraints": {
            "category": "electronics",
            "max_budget_cents": 40000,
            "currency": "USD",
            "brand": "Sony",
            "model": "WH-1000XM5",
            "condition": "NEW",
            "color": "black",
            "max_delivery_days": 5,
        },
        "product_snapshot": {
            "sku": "WH1000XM5-BLK-NEW",
            "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            "condition": "NEW",
            "color": "black",
        },
        "merchant_quote": {
            "merchant_name": "Apex Electronics",
            "merchant_domain": "apextech.com",
            "sku": "WH1000XM5-BLK-NEW",
            "subtotal_cents": 39900,
            "shipping_cents": 0,
            "tax_cents": 0,
            "total_cents": 39900,
            "currency": "USD",
            "estimated_delivery_days": 3,
        },
    }
    rc_resp = client.post("/receipts/compile", json=receipt_payload)
    assert rc_resp.status_code == 200
    receipt_hash = rc_resp.json()["receipt_hash"]

    # Approve receipt
    appr_resp = client.post(f"/receipts/{purchase_id}/approve", json={"receipt_hash": receipt_hash})
    assert appr_resp.status_code == 200

    # 3. Before fulfillment, gate returns HOLD (awaiting carrier telemetry)
    gate_resp = client.get(f"/purchases/{purchase_id}/gate")
    assert gate_resp.status_code == 200
    assert gate_resp.json()["outcome"] == "HOLD"
    assert gate_resp.json()["status_pill"] == "HOLD"
    assert gate_resp.json()["can_capture"] is False

    # Attempt capture: must be blocked by gate (409 Conflict)
    cap_blocked_resp = client.post(f"/purchases/{purchase_id}/capture")
    assert cap_blocked_resp.status_code == 409
    assert cap_blocked_resp.json()["detail"]["error"] == "CAPTURE_BLOCKED_BY_GATE"

    # 4. Ingest Refurbished evidence via scenario console
    scen_resp = client.post(f"/fulfillment/scenarios/{purchase_id}", json={"scenario": "refurbished"})
    assert scen_resp.status_code == 200
    assert scen_resp.json()["gate_outcome"] == "DRIFT"
    assert scen_resp.json()["status_pill"] == "CAPTURE BLOCKED"

    # Verify gate endpoint reflects DRIFT
    gate_resp2 = client.get(f"/purchases/{purchase_id}/gate")
    assert gate_resp2.status_code == 200
    assert gate_resp2.json()["outcome"] == "DRIFT"
    assert gate_resp2.json()["status_pill"] == "CAPTURE BLOCKED"

    # 5. Ingest seller correction via scenario console
    scen_resp2 = client.post(f"/fulfillment/scenarios/{purchase_id}", json={"scenario": "corrected"})
    assert scen_resp2.status_code == 200
    assert scen_resp2.json()["gate_outcome"] == "MATCH"
    assert scen_resp2.json()["status_pill"] == "AUTHORIZED · NOT CAPTURED"

    # 6. Capture is now allowed
    cap_resp = client.post(f"/purchases/{purchase_id}/capture")
    assert cap_resp.status_code == 200
    assert cap_resp.json()["status"] == "COMPLETED"

    # 7. Check 10-step Replay endpoint
    replay_resp = client.get(f"/purchases/{purchase_id}/replay-timeline")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert len(replay_data["steps"]) == 10
    assert replay_data["chain_intact"] is True
    assert replay_data["steps"][9]["status"] == "COMPLETED"

    # 8. Check evidence list endpoint
    ev_list_resp = client.get(f"/purchases/{purchase_id}/evidence")
    assert ev_list_resp.status_code == 200
    assert len(ev_list_resp.json()) >= 2
