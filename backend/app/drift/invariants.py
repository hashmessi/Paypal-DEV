"""Deterministic Invariant verification rules (DRIFT-01, DRIFT-03, PAY-07)."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from app.core.models import FulfillmentEvidence, PaymentAuthorization, PromiseReceipt
from app.drift.models import Finding, Severity


def check_auth_expiry(
    auth: Optional[PaymentAuthorization],
    now: datetime,
) -> List[Finding]:
    """INV-06 (PAY-07): Check authorization honor period and expiration time."""
    findings: List[Finding] = []
    if not auth:
        return findings

    # Ensure now has timezone for comparison
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if auth.expiration_time:
        exp_time = auth.expiration_time
        if exp_time.tzinfo is None:
            exp_time = exp_time.replace(tzinfo=timezone.utc)

        if now >= exp_time:
            findings.append(
                Finding(
                    invariant_code="INV-06-EXPIRY",
                    severity=Severity.BLOCKER,
                    message=f"Authorization expired on {exp_time.isoformat()}. Capture prohibited (RENEWAL_REQUIRED).",
                    expected=f"< {exp_time.isoformat()}",
                    actual=now.isoformat(),
                )
            )

    return findings


def check_amount_binding(
    receipt: PromiseReceipt,
    auth: Optional[PaymentAuthorization],
) -> List[Finding]:
    """INV-07 (PAY-02): the authorization must hold exactly the buyer-approved receipt total."""
    if not auth:
        return []
    if auth.amount_cents == receipt.total_cents and auth.currency == receipt.currency:
        return []
    return [
        Finding(
            invariant_code="INV-07-AMOUNT",
            severity=Severity.BLOCKER,
            message="Authorized amount does not match the approved Promise Receipt total. Capture blocked.",
            expected=f"{receipt.total_cents} {receipt.currency}",
            actual=f"{auth.amount_cents} {auth.currency}",
        )
    ]


def check_fulfillment_invariants(
    receipt: PromiseReceipt,
    evidence_list: List[FulfillmentEvidence],
    now: datetime,
) -> List[Finding]:
    """Evaluate fulfillment telemetry against receipt capture conditions."""
    findings: List[Finding] = []

    # Parse capture conditions & constraints from receipt
    try:
        conditions = json.loads(receipt.capture_conditions_json)
    except Exception:
        conditions = {}

    expected_sku = conditions.get("expected_sku")
    expected_color = conditions.get("expected_color")
    reject_refurb = conditions.get("reject_refurbished", True)

    if not evidence_list:
        findings.append(
            Finding(
                invariant_code="INV-03-CARRIER",
                severity=Severity.INFO,
                message="Awaiting carrier telemetry. No fulfillment evidence received yet.",
            )
        )
        return findings

    # Sort evidence by sequence ascending
    sorted_ev = sorted(evidence_list, key=lambda e: e.seq)
    latest_ev = sorted_ev[-1]

    def latest_with(attr: str) -> Optional[FulfillmentEvidence]:
        # A later event that omits a field must not erase an earlier observation of it.
        return next((e for e in reversed(sorted_ev) if getattr(e, attr)), None)

    cond_ev, sku_ev, color_ev = latest_with("condition"), latest_with("sku"), latest_with("color")

    # INV-01: Physical Condition Invariant
    if cond_ev:
        cond_upper = cond_ev.condition.upper()
        if reject_refurb and cond_upper == "REFURBISHED":
            findings.append(
                Finding(
                    invariant_code="INV-01-CONDITION",
                    severity=Severity.BLOCKER,
                    message=f"Condition drift detected: buyer approved Brand New, but seller fulfilled REFURBISHED.",
                    evidence_id=cond_ev.id,
                    expected="NEW",
                    actual="REFURBISHED",
                )
            )
        elif reject_refurb and cond_upper == "UNVERIFIED":
            findings.append(
                Finding(
                    invariant_code="INV-01-CONDITION",
                    severity=Severity.BLOCKER,
                    message="Condition drift detected: fulfilled item condition is UNVERIFIED.",
                    evidence_id=cond_ev.id,
                    expected="NEW",
                    actual="UNVERIFIED",
                )
            )

    # INV-02: SKU & Color Invariants
    if sku_ev and expected_sku:
        if sku_ev.sku.strip() != expected_sku.strip():
            findings.append(
                Finding(
                    invariant_code="INV-02-SKU",
                    severity=Severity.BLOCKER,
                    message=f"SKU mismatch: expected '{expected_sku}', fulfilled '{sku_ev.sku}'.",
                    evidence_id=sku_ev.id,
                    expected=expected_sku,
                    actual=sku_ev.sku,
                )
            )

    if color_ev and expected_color:
        if color_ev.color.strip().lower() != expected_color.strip().lower():
            findings.append(
                Finding(
                    invariant_code="INV-02-COLOR",
                    severity=Severity.BLOCKER,
                    message=f"Color mismatch: expected '{expected_color}', fulfilled '{color_ev.color}'.",
                    evidence_id=color_ev.id,
                    expected=expected_color,
                    actual=color_ev.color,
                )
            )

    # INV-03 & INV-05: Carrier Acceptance & Trust Ladder
    # Check if ANY valid carrier telemetry has reached ACCEPTED, IN_TRANSIT, or DELIVERED
    has_carrier_acceptance = any(
        e.trust_level == "CARRIER_TELEMETRY"
        and e.carrier_status in ("ACCEPTED", "IN_TRANSIT", "DELIVERED")
        for e in sorted_ev
    )

    if not has_carrier_acceptance:
        # Check if we only have LABEL_CREATED
        has_label_only = any(
            e.carrier_status == "LABEL_CREATED" for e in sorted_ev
        )
        if has_label_only:
            findings.append(
                Finding(
                    invariant_code="INV-03-CARRIER",
                    severity=Severity.WARNING,
                    message="Carrier has only created shipping label. Awaiting physical carrier package acceptance.",
                    evidence_id=latest_ev.id,
                    expected="ACCEPTED",
                    actual="LABEL_CREATED",
                )
            )
        else:
            findings.append(
                Finding(
                    invariant_code="INV-05-TRUST",
                    severity=Severity.WARNING,
                    message="Carrier acceptance required before settlement. Merchant claims alone cannot satisfy carrier telemetry.",
                    evidence_id=latest_ev.id,
                    expected="CARRIER_TELEMETRY (ACCEPTED)",
                    actual=latest_ev.trust_level,
                )
            )

    # INV-04: ETA Invariant
    if latest_ev.eta:
        max_days = conditions.get("max_delivery_days", 5)
        # Calculate maximum allowed deadline
        receipt_created = receipt.created_at
        if receipt_created.tzinfo is None:
            receipt_created = receipt_created.replace(tzinfo=timezone.utc)

        eta_dt = latest_ev.eta
        if eta_dt.tzinfo is None:
            eta_dt = eta_dt.replace(tzinfo=timezone.utc)

        allowed_deadline = receipt_created.timestamp() + (max_days * 86400)
        if eta_dt.timestamp() > allowed_deadline:
            findings.append(
                Finding(
                    invariant_code="INV-04-ETA",
                    severity=Severity.WARNING,
                    message=f"Carrier ETA ({eta_dt.strftime('%Y-%m-%d')}) exceeds buyer promised deadline ({max_days} days).",
                    evidence_id=latest_ev.id,
                    expected=f"within {max_days} days",
                    actual=eta_dt.isoformat(),
                )
            )

    return findings

