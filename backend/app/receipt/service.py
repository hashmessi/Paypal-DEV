"""Promise Receipt Service managing creation, approval, and versioning lifecycle."""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import canonical_json
from app.core.clock import Clock, SystemClock
from app.core.models import DecisionEvent, PromiseReceipt, Purchase
from app.ledger.events import append_event
from app.receipt.compiler import compile_canonical_receipt
from app.receipt.models import (
    ApprovedReceiptImmutableError,
    BudgetExceededError,
    PurchaseNotFoundError,
    StaleReceiptHashError,
)

logger = logging.getLogger(__name__)


class ReceiptService:
    """Orchestrates receipt compilation, versioning, buyer approval, and audit trails."""

    def __init__(self, db: Session, clock: Optional[Clock] = None) -> None:
        self.db = db
        self.clock = clock or SystemClock()

    def get_latest_receipt(self, purchase_id: str) -> Optional[PromiseReceipt]:
        stmt = (
            select(PromiseReceipt)
            .where(PromiseReceipt.purchase_id == purchase_id)
            .order_by(PromiseReceipt.version.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def compile_receipt(
        self,
        purchase_id: str,
        constraints: Dict[str, Any],
        product_snapshot: Dict[str, Any],
        merchant_quote: Dict[str, Any],
    ) -> PromiseReceipt:
        """Compile a new draft Promise Receipt or advance version if terms changed."""
        purchase = self.db.get(Purchase, purchase_id)
        if not purchase:
            raise PurchaseNotFoundError(purchase_id)

        current_receipt = self.get_latest_receipt(purchase_id)
        next_version = (current_receipt.version + 1) if current_receipt else 1

        canon_str, r_hash, payload = compile_canonical_receipt(
            constraints=constraints,
            product_snapshot=product_snapshot,
            merchant_quote=merchant_quote,
            version=next_version,
        )

        receipt = PromiseReceipt(
            purchase_id=purchase_id,
            version=next_version,
            status="draft",
            receipt_hash=r_hash,
            canonical_payload=canon_str,
            constraints_json=canonical_json(constraints),
            product_snapshot_json=canonical_json(product_snapshot),
            merchant_quote_json=canonical_json(merchant_quote),
            capture_conditions_json=canonical_json(payload["capture_conditions"]),
            total_cents=payload["total_cents"],
            currency=payload["currency"],
        )
        self.db.add(receipt)
        self.db.flush()

        # Append to decision ledger
        append_event(
            session=self.db,
            purchase_id=purchase_id,
            event_type="RECEIPT_COMPILED",
            actor="shopper_agent",
            payload={
                "receipt_id": receipt.id,
                "version": next_version,
                "receipt_hash": r_hash,
                "total_cents": payload["total_cents"],
            },
            clock=self.clock,
        )

        self.db.commit()
        return receipt

    def approve_receipt(self, purchase_id: str, approved_hash: str) -> PromiseReceipt:
        """Buyer approves the exact Promise Receipt hash.

        Enforces:
        - RCPT-03: Approving a non-current or stale hash raises StaleReceiptHashError (409 Conflict).
        - Approved receipts cannot have their financial terms modified.
        - Appends RECEIPT_APPROVED to decision ledger.
        """
        receipt = self.get_latest_receipt(purchase_id)
        if not receipt:
            raise ValueError(f"No receipt found for purchase {purchase_id}")

        if receipt.receipt_hash != approved_hash:
            raise StaleReceiptHashError(
                expected_hash=receipt.receipt_hash,
                provided_hash=approved_hash,
            )

        if receipt.status == "approved":
            # Idempotent re-assertion
            return receipt

        now_dt = self.clock.now()
        receipt.status = "approved"
        receipt.approved_at = now_dt

        purchase = self.db.get(Purchase, purchase_id)
        if purchase:
            purchase.receipt_hash = approved_hash
            purchase.version = receipt.version
            purchase.status = "receipt_approved"

        append_event(
            session=self.db,
            purchase_id=purchase_id,
            event_type="RECEIPT_APPROVED",
            actor="buyer",
            payload={
                "receipt_id": receipt.id,
                "version": receipt.version,
                "receipt_hash": approved_hash,
                "approved_at": now_dt.isoformat(),
            },
            clock=self.clock,
        )

        self.db.commit()
        return receipt

    def handle_merchant_term_change(
        self,
        purchase_id: str,
        new_merchant_quote: Dict[str, Any],
    ) -> PromiseReceipt:
        """RCPT-04: Merchant modifies terms (e.g. price adjustment, delivery shift).

        Marks prior approved receipt as STALE and compiles new version requiring fresh reapproval.
        """
        prior_receipt = self.get_latest_receipt(purchase_id)
        if not prior_receipt:
            raise ValueError(f"No existing receipt found for purchase {purchase_id}")

        # Mark previous version stale
        prior_receipt.status = "stale"
        append_event(
            session=self.db,
            purchase_id=purchase_id,
            event_type="RECEIPT_STALE",
            actor="merchant",
            payload={
                "stale_version": prior_receipt.version,
                "stale_hash": prior_receipt.receipt_hash,
                "reason": "Merchant adjusted transaction terms",
            },
            clock=self.clock,
        )
        self.db.flush()

        # Parse stored constraints & snapshot to recompile next version
        constraints = json.loads(prior_receipt.constraints_json)
        product_snapshot = json.loads(prior_receipt.product_snapshot_json)

        return self.compile_receipt(
            purchase_id=purchase_id,
            constraints=constraints,
            product_snapshot=product_snapshot,
            merchant_quote=new_merchant_quote,
        )
