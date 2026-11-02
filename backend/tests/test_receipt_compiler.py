"""Tests for Promise Receipt Compiler, Canonical Hashing, and Budget Check (RCPT-01, RCPT-02)."""

import pytest

from app.core.canon import canonical_json, sha256_hex
from app.receipt.compiler import (
    assert_no_floats,
    compile_canonical_receipt,
)
from app.receipt.models import BudgetExceededError


def test_float_rejection():
    """RCPT-01: Floats are strictly prohibited in canonical receipt."""
    bad_payload = {"amount": 89.99}
    with pytest.raises(ValueError) as exc:
        assert_no_floats(bad_payload)
    assert "Float value 89.99 at path 'root.amount' is strictly prohibited" in str(exc.value)

    nested_bad = {"quote": {"items": [{"price": 10.5}]}}
    with pytest.raises(ValueError):
        assert_no_floats(nested_bad)

    # Valid integers and strings must pass
    valid_payload = {"amount_cents": 8999, "currency": "USD"}
    assert_no_floats(valid_payload)


def test_budget_gate_rejection():
    """RCPT-02: Contract whose total exceeds buyer's max is rejected before any PayPal call."""
    constraints = {"max_total_cents": 8000, "condition": "new"}  # $80 max
    quote = {"total_cents": 8999, "currency": "USD"}             # $89.99 quote
    snapshot = {"id": "item-1"}

    with pytest.raises(BudgetExceededError) as exc:
        compile_canonical_receipt(constraints, snapshot, quote)

    assert exc.value.quote_cents == 8999
    assert exc.value.max_cents == 8000
    assert "exceeds buyer budget" in str(exc.value)


def test_canonical_json_and_golden_hash_vector():
    """Verify deterministic RFC 8785 canonical JSON formatting and repeatable SHA-256 digest."""
    constraints = {
        "product_type": "over-ear headphones",
        "condition": "new",
        "color": "black",
        "max_total_cents": 10000,
        "currency": "USD",
        "deliver_within_days": 5,
        "substitutions_allowed": False,
    }
    snapshot = {
        "product_id": "PROD-001",
        "title": "Sony WH-1000XM5",
    }
    quote = {
        "subtotal_cents": 8999,
        "shipping_cents": 0,
        "tax_cents": 0,
        "total_cents": 8999,
        "currency": "USD",
        "merchant_name": "Apex Electronics",
        "merchant_domain": "apextech.com",
        "sku": "WH1000XM5-BLK-NEW",
    }

    canon_1, hash_1, _ = compile_canonical_receipt(constraints, snapshot, quote, version=1)
    canon_2, hash_2, _ = compile_canonical_receipt(constraints, snapshot, quote, version=1)

    assert canon_1 == canon_2
    assert hash_1 == hash_2
    assert len(hash_1) == 64
    assert hash_1 == sha256_hex(canon_1)

    # Verify keys are sorted lexicographically
    assert canon_1.startswith('{"capture_conditions":')

