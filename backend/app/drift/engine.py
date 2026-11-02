"""Pure deterministic Invariant Gate Evaluation Engine (DRIFT-01, DRIFT-02)."""

from datetime import datetime, timezone
from typing import List, Optional

from app.core.models import FulfillmentEvidence, PaymentAuthorization, PromiseReceipt
from app.drift.explainer import generate_explanation
from app.drift.invariants import check_auth_expiry, check_fulfillment_invariants
from app.drift.models import Finding, GateEvaluation, GateOutcome, Severity


def evaluate(
    receipt: PromiseReceipt,
    auth: Optional[PaymentAuthorization],
    evidence_list: List[FulfillmentEvidence],
    now: datetime,
) -> GateEvaluation:
    """Evaluate all invariants deterministically.

    Returns GateEvaluation with outcome MATCH | DRIFT | HOLD | PROHIBITED.
    """
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    findings: List[Finding] = []

    # 1. Check authorization expiration
    expiry_findings = check_auth_expiry(auth=auth, now=now)
    findings.extend(expiry_findings)

    # 2. Check fulfillment telemetry invariants
    fulf_findings = check_fulfillment_invariants(receipt=receipt, evidence_list=evidence_list, now=now)
    findings.extend(fulf_findings)

    # 3. Determine Outcome
    has_expiry_blocker = any(f.invariant_code == "INV-06-EXPIRY" for f in findings)
    has_drift_blocker = any(f.severity == Severity.BLOCKER and f.invariant_code != "INV-06-EXPIRY" for f in findings)
    has_warning = any(f.severity == Severity.WARNING for f in findings)
    has_info = any(f.severity == Severity.INFO for f in findings)

    if has_expiry_blocker:
        outcome = GateOutcome.PROHIBITED
    elif has_drift_blocker:
        outcome = GateOutcome.DRIFT
    elif has_warning or has_info:
        outcome = GateOutcome.HOLD
    else:
        outcome = GateOutcome.MATCH

    # 4. Status pill derivation
    if auth and auth.state == "captured":
        status_pill = "CAPTURED"
    elif outcome == GateOutcome.PROHIBITED:
        status_pill = "RENEWAL_REQUIRED"
    elif outcome == GateOutcome.DRIFT:
        status_pill = "CAPTURE BLOCKED"
    elif outcome == GateOutcome.HOLD:
        status_pill = "HOLD"
    else:
        status_pill = "AUTHORIZED · NOT CAPTURED"

    can_capture = (outcome == GateOutcome.MATCH) and (auth is None or auth.state in ("authorized", "approved"))
    explanation = generate_explanation(outcome, findings)

    return GateEvaluation(
        outcome=outcome,
        status_pill=status_pill,
        findings=findings,
        can_capture=can_capture,
        explanation=explanation,
        evaluated_at=now,
    )

