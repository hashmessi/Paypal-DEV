"""Google Agent Payments Protocol (AP2) v0.2 Mandate Mapping.

PromiseLoop aligns with and extends AP2 by carrying the approved mandate
past checkout into fulfillment-gated settlement:
- AP2 Open Checkout Mandate: natural-language intent frozen into typed constraints.
- AP2 Closed Checkout Mandate: bound to the RFC 8785 canonical hash (checkout_hash).
- PromiseLoop Extension: conditional capture rules enforcing invariant fulfillment match.
"""

import json
from typing import Any, Dict
from app.core.models import PromiseReceipt, Purchase


def _parse_field(val: Any) -> Dict[str, Any]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val.strip():
        try:
            return json.loads(val)
        except Exception:
            return {}
    return {}


def compile_ap2_mandate(receipt: PromiseReceipt, purchase: Purchase) -> Dict[str, Any]:
    """Compile a PromiseReceipt into standard AP2 v0.2 Open and Closed Checkout Mandates."""
    constraints = _parse_field(getattr(receipt, "constraints_json", None) or getattr(receipt, "constraints", None))
    product_snapshot = _parse_field(getattr(receipt, "product_snapshot_json", None) or getattr(receipt, "product_snapshot", None))
    merchant_quote = _parse_field(getattr(receipt, "merchant_quote_json", None) or getattr(receipt, "merchant_quote", None))
    capture_conditions = _parse_field(getattr(receipt, "capture_conditions_json", None) or getattr(receipt, "capture_conditions", None))

    purchase_id = purchase.id
    receipt_hash = receipt.receipt_hash

    # AP2 Open Checkout Mandate: Buyer authorization boundaries before cart selection
    open_mandate: Dict[str, Any] = {
        "@type": "ap2:open_checkout_mandate:v0.2",
        "mandate_id": f"urn:ap2:mandate:open:{purchase_id}",
        "version": "0.2",
        "intent_type": "COMMERCE_PURCHASE",
        "user_authorization": {
            "status": "APPROVED",
            "instruction": purchase.buyer_instruction or constraints.get("product_type", ""),
            "approved_at": receipt.approved_at.isoformat() if receipt.approved_at else None,
        },
        "constraints": {
            "product_type": constraints.get("product_type", ""),
            "condition": constraints.get("condition", "new"),
            "variant": constraints.get("variant_color") or constraints.get("color"),
            "max_total": {
                "amount_cents": constraints.get("max_total_cents") or receipt.total_cents,
                "currency": receipt.currency or "USD",
            },
            "delivery_deadline_days": constraints.get("deliver_within_days") or constraints.get("deadline_days", 5),
            "allow_substitutions": constraints.get("substitution_allowed", False),
        },
        "merchant_allowlist": [
            merchant_quote.get("seller_domain") or "demomerchant.example.com"
        ],
        "created_at": receipt.created_at.isoformat() if receipt.created_at else None,
    }

    # AP2 Closed Checkout Mandate: Bound to exact checkout contract hash
    closed_mandate: Dict[str, Any] = {
        "@type": "ap2:closed_checkout_mandate:v0.2",
        "mandate_id": f"urn:ap2:mandate:closed:{purchase_id}",
        "parent_mandate_id": f"urn:ap2:mandate:open:{purchase_id}",
        "version": "0.2",
        "checkout_hash": receipt_hash,
        "line_items": [
            {
                "title": product_snapshot.get("title", constraints.get("product_type", "Item")),
                "sku": merchant_quote.get("sku", "WH1000XM5-BLK-NEW"),
                "condition": constraints.get("condition", "new"),
                "variant": constraints.get("variant_color") or constraints.get("color", "black"),
                "price_cents": receipt.total_cents,
                "quantity": 1,
            }
        ],
        "merchant": {
            "seller_domain": merchant_quote.get("seller_domain", "demomerchant.example.com"),
            "quote_id": merchant_quote.get("quote_id", f"q-{purchase_id[:8]}"),
            "promised_delivery_days": merchant_quote.get("delivery_days", 5),
        },
        "payment": {
            "provider": "PAYPAL",
            "intent": "AUTHORIZE",
            "custom_id": receipt_hash,
            "authorized_amount": {
                "amount_cents": receipt.total_cents,
                "currency": receipt.currency or "USD",
            },
        },
        "settlement_conditions": {
            "@extension": "promiseloop:settlement_gate:v1",
            "capture_trigger": "DETERMINISTIC_FULFILLMENT_MATCH",
            "require_carrier_acceptance": capture_conditions.get("require_carrier_acceptance", True),
            "reject_refurbished": capture_conditions.get("reject_refurbished", True),
            "max_delivery_days": capture_conditions.get("max_delivery_days", 5),
            "expected_sku": capture_conditions.get("expected_sku", "WH1000XM5-BLK-NEW"),
            "hold_policy": "LOCK_CAPTURE_ON_DRIFT",
        },
        "created_at": receipt.created_at.isoformat() if receipt.created_at else None,
    }

    return {
        "specification": "AP2 v0.2 (Google Agent Payments Protocol) + PromiseLoop Settlement Gate Extension",
        "mandate_version": "0.2",
        "purchase_id": purchase_id,
        "receipt_id": receipt.id,
        "receipt_version": receipt.version,
        "receipt_hash": receipt_hash,
        "status": receipt.status,
        "tamper_evident_anchor": {
            "algorithm": "SHA-256",
            "canonicalization": "RFC 8785 (JCS)",
            "paypal_binding_field": "purchase_units[0].custom_id",
        },
        "open_checkout_mandate": open_mandate,
        "closed_checkout_mandate": closed_mandate,
    }
