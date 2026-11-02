"""Data models and exceptions for Promise Receipts."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class ReceiptError(Exception):
    """Base exception for Promise Receipt operations."""
    pass


class PurchaseNotFoundError(ReceiptError):
    """Raised when purchase ID does not exist."""
    def __init__(self, purchase_id: str) -> None:
        super().__init__(f"Purchase {purchase_id} not found")


class BudgetExceededError(ReceiptError):
    """RCPT-02: Raised when merchant quote total exceeds buyer's maximum budget."""

    def __init__(self, quote_cents: int, max_cents: int) -> None:
        self.quote_cents = quote_cents
        self.max_cents = max_cents
        super().__init__(
            f"Merchant total of {quote_cents} cents (${quote_cents/100:.2f}) "
            f"exceeds buyer budget of {max_cents} cents (${max_cents/100:.2f})"
        )


class StaleReceiptHashError(ReceiptError):
    """RCPT-03: Raised when buyer approves a non-current receipt hash (HTTP 409)."""

    def __init__(self, expected_hash: str, provided_hash: str) -> None:
        self.expected_hash = expected_hash
        self.provided_hash = provided_hash
        super().__init__(
            f"Stale receipt hash: attempted approval of hash {provided_hash[:12]}..., "
            f"but active receipt hash is {expected_hash[:12]}..."
        )


class ApprovedReceiptImmutableError(ReceiptError):
    """RCPT-04: Raised when attempting to mutate an already approved receipt."""

    def __init__(self, receipt_id: str) -> None:
        super().__init__(f"Approved receipt {receipt_id} is immutable and cannot be updated.")


class CompileReceiptRequest(BaseModel):
    purchase_id: str
    constraints: Dict[str, Any]
    product_snapshot: Dict[str, Any]
    merchant_quote: Dict[str, Any]


class ApproveReceiptRequest(BaseModel):
    receipt_hash: str = Field(..., description="The exact SHA-256 hash buyer approved")
