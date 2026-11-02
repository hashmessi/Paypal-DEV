"""Tests verifying PayPal Order custom_id is bound to receipt hash (PAY-08)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.models import Purchase
from app.payments.fake import FakeGateway


def test_paypal_order_carries_receipt_hash_custom_id(client: TestClient, fake_gateway: FakeGateway):
    """PAY-08: PayPal Order carries the receipt hash in custom_id."""
    test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    resp = client.post(
        "/checkout/orders",
        json={
            "ref": "ORD-BOUND-001",
            "amount_cents": 8999,
            "currency": "USD",
            "receipt_hash": test_hash,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    order_id = data["order_id"]

    # Verify FakeGateway order captured custom_id
    gw_order = fake_gateway.orders.get(order_id)
    assert gw_order is not None
    assert gw_order.get("custom_id") == test_hash


def test_end_to_end_receipt_and_checkout_flow(client: TestClient):
    """Complete Phase 2 integration flow:

    1. Extract intent
    2. Search candidates
    3. Generate quote
    4. Compile receipt
    5. Approve receipt
    6. Mismatched approve returns 409 Conflict
    7. Create PayPal order bound to receipt hash
    """
    # 1. Extract Intent
    intent_resp = client.post(
        "/intent/extract",
        json={"instruction": "new black over-ear headphones under $100, arrive within 5 days"},
    )
    assert intent_resp.status_code == 200
    intent_data = intent_resp.json()
    constraints = intent_data["constraints"]
    assert constraints["max_total_cents"] == 10000

    # 2. Search candidates
    search_resp = client.get("/discovery/search?q=headphones")
    assert search_resp.status_code == 200
    candidates = search_resp.json()
    assert len(candidates) > 0
    candidate = candidates[0]
    offer = candidate["offers"][0]

    # 3. Generate quote
    quote_resp = client.post("/discovery/quote", json={"offer_id": offer["offer_id"]})
    assert quote_resp.status_code == 200
    quote = quote_resp.json()

    # Pre-create purchase for receipt
    init_order_resp = client.post(
        "/checkout/orders",
        json={"ref": "ORD-SHOP-01", "amount_cents": quote["total_cents"], "currency": "USD"},
    )
    purchase_id = init_order_resp.json()["purchase_id"]

    # 4. Compile receipt
    compile_resp = client.post(
        "/receipts/compile",
        json={
            "purchase_id": purchase_id,
            "constraints": constraints,
            "product_snapshot": candidate,
            "merchant_quote": quote,
        },
    )
    assert compile_resp.status_code == 200
    receipt = compile_resp.json()
    receipt_hash = receipt["receipt_hash"]
    assert len(receipt_hash) == 64

    # 5. Stale / bad hash approval fails with 409 Conflict
    bad_approve_resp = client.post(
        f"/receipts/{purchase_id}/approve",
        json={"receipt_hash": "f" * 64},
    )
    assert bad_approve_resp.status_code == 409

    # 6. Valid approval succeeds
    good_approve_resp = client.post(
        f"/receipts/{purchase_id}/approve",
        json={"receipt_hash": receipt_hash},
    )
    assert good_approve_resp.status_code == 200
    assert good_approve_resp.json()["status"] == "approved"

    # 7. Create PayPal order bound to approved receipt hash
    bound_order_resp = client.post(
        "/checkout/orders",
        json={
            "ref": "ORD-SHOP-01-AUTH",
            "amount_cents": quote["total_cents"],
            "currency": "USD",
            "receipt_hash": receipt_hash,
        },
    )
    assert bound_order_resp.status_code == 201
