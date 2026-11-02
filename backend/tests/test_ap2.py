"""Test Google Agent Payments Protocol (AP2) v0.2 Mandate compilation & endpoint."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.clock import FixedClock
from app.core.models import PromiseReceipt, Purchase
from app.receipt.ap2 import compile_ap2_mandate
from app.main import app


def test_compile_ap2_mandate_structure():
    fixed_now = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc)
    purchase = Purchase(
        id="pur-test-01",
        ref="PL-TEST-001",
        buyer_instruction="Sony WH-1000XM5 black under $400, no refurbished",
        status="approved",
    )
    receipt = PromiseReceipt(
        id="rcpt-test-01",
        purchase_id="pur-test-01",
        version=1,
        status="approved",
        receipt_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        total_cents=39900,
        currency="USD",
        constraints_json='{"product_type": "Over-ear headphones", "condition": "new", "variant_color": "black", "max_total_cents": 40000, "deliver_within_days": 5}',
        product_snapshot_json='{"title": "Sony WH-1000XM5 Noise Canceling Headphones - Black", "sku": "WH1000XM5-BLK-NEW"}',
        merchant_quote_json='{"seller_domain": "bestbuy.example.com", "total_cents": 39900, "sku": "WH1000XM5-BLK-NEW", "delivery_days": 3}',
        capture_conditions_json='{"require_carrier_acceptance": true, "reject_refurbished": true, "max_delivery_days": 5, "expected_sku": "WH1000XM5-BLK-NEW"}',
        approved_at=fixed_now,
        created_at=fixed_now,
    )

    mandate_doc = compile_ap2_mandate(receipt, purchase)

    assert mandate_doc["mandate_version"] == "0.2"
    assert mandate_doc["purchase_id"] == "pur-test-01"
    assert mandate_doc["receipt_hash"] == receipt.receipt_hash

    open_m = mandate_doc["open_checkout_mandate"]
    assert open_m["@type"] == "ap2:open_checkout_mandate:v0.2"
    assert open_m["mandate_id"] == "urn:ap2:mandate:open:pur-test-01"
    assert open_m["user_authorization"]["status"] == "APPROVED"
    assert open_m["constraints"]["condition"] == "new"
    assert open_m["constraints"]["max_total"]["amount_cents"] == 40000

    closed_m = mandate_doc["closed_checkout_mandate"]
    assert closed_m["@type"] == "ap2:closed_checkout_mandate:v0.2"
    assert closed_m["checkout_hash"] == receipt.receipt_hash
    assert closed_m["payment"]["provider"] == "PAYPAL"
    assert closed_m["payment"]["custom_id"] == receipt.receipt_hash
    assert closed_m["settlement_conditions"]["@extension"] == "promiseloop:settlement_gate:v1"
    assert closed_m["settlement_conditions"]["reject_refurbished"] is True


def test_ap2_endpoint_with_client(client: TestClient):
    demo_res = client.post("/demo/run", json={})
    assert demo_res.status_code == 200
    purchase_id = demo_res.json()["purchase_id"]

    resp = client.get(f"/receipts/{purchase_id}/ap2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["mandate_version"] == "0.2"
    assert data["purchase_id"] == purchase_id
    assert "open_checkout_mandate" in data
    assert "closed_checkout_mandate" in data
    assert data["closed_checkout_mandate"]["checkout_hash"] == data["receipt_hash"]

