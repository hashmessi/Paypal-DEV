"""RFC 8785 Canonical JSON compiler and SHA-256 hash sealing for Promise Receipts."""

from decimal import Decimal
from typing import Any, Dict, Tuple

from app.core.canon import canonical_json, sha256_hex
from app.receipt.models import BudgetExceededError


def assert_no_floats(obj: Any, path: str = "root") -> None:
    """RCPT-01: Prohibit floating-point representations for money in Promise Receipt.

    All money and contract values must be exact integer minor units (cents).
    Third-party raw product snapshot metadata is preserved as raw data.
    """
    if "product_snapshot" in path:
        return

    if isinstance(obj, float):
        raise ValueError(
            f"Float value {obj} at path '{path}' is strictly prohibited in Promise Receipt. "
            f"Use integer minor units (cents) to avoid rounding ambiguities."
        )
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            assert_no_floats(item, f"{path}[{idx}]")


def build_capture_conditions(constraints: Dict[str, Any], merchant_quote: Dict[str, Any]) -> Dict[str, Any]:
    """Derive deterministic capture invariant rules embedded in receipt."""
    req_condition = constraints.get("condition", "new").upper()
    reject_refurb = (req_condition == "NEW")

    return {
        "require_carrier_acceptance": True,
        "reject_label_created_alone": True,
        "reject_refurbished": reject_refurb,
        "max_delivery_days": constraints.get("deliver_within_days", 5),
        "expected_sku": merchant_quote.get("sku", "WH1000XM5-BLK-NEW"),
        "expected_color": constraints.get("color"),
    }


def compile_canonical_receipt(
    constraints: Dict[str, Any],
    product_snapshot: Dict[str, Any],
    merchant_quote: Dict[str, Any],
    version: int = 1,
) -> Tuple[str, str, Dict[str, Any]]:
    """Compile and cryptographically seal a Promise Receipt.

    Enforces:
    - RCPT-01: Canonical RFC 8785 JSON formatting, integer minor units, float rejection.
    - RCPT-02: Budget check — if merchant quote total exceeds max budget, raises BudgetExceededError.

    Returns:
        (canonical_json_string, receipt_hash_sha256, sealed_payload_dict)
    """
    # 1. Budget enforcement (RCPT-02)
    max_budget = constraints.get("max_total_cents")
    quote_total = merchant_quote.get("total_cents")

    if max_budget is not None and quote_total is not None:
        if quote_total > max_budget:
            raise BudgetExceededError(quote_cents=quote_total, max_cents=max_budget)

    # 2. Derive capture conditions
    capture_conditions = build_capture_conditions(constraints, merchant_quote)

    # 3. Assemble complete sealed payload
    payload: Dict[str, Any] = {
        "version": version,
        "currency": merchant_quote.get("currency", "USD"),
        "total_cents": quote_total,
        "constraints": constraints,
        "product_snapshot": product_snapshot,
        "merchant_quote": merchant_quote,
        "capture_conditions": capture_conditions,
    }

    # 4. Prohibit floats across entire payload tree
    assert_no_floats(payload)

    # 5. Format to RFC 8785 canonical JSON
    canon_str = canonical_json(payload)

    # 6. Compute SHA-256 digest
    receipt_hash = sha256_hex(canon_str)

    return canon_str, receipt_hash, payload
