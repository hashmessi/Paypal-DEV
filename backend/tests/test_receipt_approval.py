"""Tests for Receipt Approval Gate and Versioning (RCPT-03, RCPT-04)."""

import pytest
from sqlalchemy.orm import Session

from app.core.clock import FixedClock
from app.core.models import DecisionEvent, PromiseReceipt, Purchase
from app.receipt.models import StaleReceiptHashError
from app.receipt.service import ReceiptService


@pytest.fixture
def purchase_and_receipt(db_session: Session, fixed_clock: FixedClock):
    purchase = Purchase(ref="PURCH-RCPT-01", buyer_instruction="Test purchase", status="draft")
    db_session.add(purchase)
    db_session.commit()

    service = ReceiptService(db=db_session, clock=fixed_clock)
    constraints = {"max_total_cents": 10000, "condition": "new", "color": "black"}
    snapshot = {"product_id": "PROD-SONY"}
    quote = {"total_cents": 8999, "currency": "USD", "sku": "WH1000XM5-BLK"}

    receipt = service.compile_receipt(purchase.id, constraints, snapshot, quote)
    return purchase, receipt, service


def test_exact_hash_approval(db_session: Session, purchase_and_receipt):
    """RCPT-03: Buyer approves exact current receipt hash."""
    purchase, receipt, service = purchase_and_receipt

    approved = service.approve_receipt(purchase.id, receipt.receipt_hash)
    assert approved.status == "approved"
    assert approved.approved_at is not None

    db_session.refresh(purchase)
    assert purchase.receipt_hash == receipt.receipt_hash
    assert purchase.status == "receipt_approved"

    # Verify decision ledger logged RECEIPT_APPROVED
    ev = (
        db_session.query(DecisionEvent)
        .filter(DecisionEvent.purchase_id == purchase.id, DecisionEvent.event_type == "RECEIPT_APPROVED")
        .first()
    )
    assert ev is not None


def test_stale_or_mismatched_hash_raises_error(purchase_and_receipt):
    """RCPT-03: Approving a non-current receipt hash raises StaleReceiptHashError."""
    purchase, receipt, service = purchase_and_receipt

    wrong_hash = "0" * 64
    with pytest.raises(StaleReceiptHashError) as exc:
        service.approve_receipt(purchase.id, wrong_hash)

    assert exc.value.expected_hash == receipt.receipt_hash
    assert exc.value.provided_hash == wrong_hash
    assert "Stale receipt hash" in str(exc.value)


def test_merchant_term_change_creates_stale_and_new_version(db_session: Session, purchase_and_receipt):
    """RCPT-04: Merchant term change marks old version STALE and compiles version 2."""
    purchase, receipt_v1, service = purchase_and_receipt

    # First approve v1
    service.approve_receipt(purchase.id, receipt_v1.receipt_hash)

    # Merchant changes price from $89.99 to $92.00
    new_quote = {"total_cents": 9200, "currency": "USD", "sku": "WH1000XM5-BLK"}
    receipt_v2 = service.handle_merchant_term_change(purchase.id, new_quote)

    db_session.refresh(receipt_v1)
    assert receipt_v1.status == "stale"
    assert receipt_v2.version == 2
    assert receipt_v2.status == "draft"
    assert receipt_v2.total_cents == 9200
    assert receipt_v2.receipt_hash != receipt_v1.receipt_hash

    # Approving with old v1 hash must now fail with StaleReceiptHashError
    with pytest.raises(StaleReceiptHashError):
        service.approve_receipt(purchase.id, receipt_v1.receipt_hash)

    # Approving with new v2 hash succeeds
    approved_v2 = service.approve_receipt(purchase.id, receipt_v2.receipt_hash)
    assert approved_v2.status == "approved"

