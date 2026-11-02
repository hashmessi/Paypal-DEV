"""Plain-language explanation generator for gate findings (DRIFT-04, SEC-02)."""

from typing import List
from app.drift.models import Finding, GateOutcome, Severity


def generate_explanation(outcome: GateOutcome, findings: List[Finding]) -> str:
    """Generate concise, deterministic plain-language summary for buyers and judges."""
    if outcome == GateOutcome.MATCH:
        return "All promise invariants verified. Fulfillment evidence strictly matches the buyer-approved Promise Receipt. Funds are cleared for capture."

    blockers = [f for f in findings if f.severity == Severity.BLOCKER]
    warnings = [f for f in findings if f.severity == Severity.WARNING]

    if outcome == GateOutcome.PROHIBITED:
        expiry_msgs = [f.message for f in blockers if "EXPIRY" in f.invariant_code]
        if expiry_msgs:
            return expiry_msgs[0]
        return "Authorization has expired. Capture is prohibited until reauthorization is renewed."

    if outcome == GateOutcome.DRIFT:
        reasons = []
        for b in blockers:
            if "CONDITION" in b.invariant_code:
                reasons.append("item condition deviates from approved terms (Refurbished vs Brand New)")
            elif "SKU" in b.invariant_code:
                reasons.append(f"fulfilled SKU does not match approved product model ({b.actual} vs {b.expected})")
            elif "COLOR" in b.invariant_code:
                reasons.append(f"fulfilled color does not match requested finish ({b.actual} vs {b.expected})")
            else:
                reasons.append(b.message)

        return f"Capture blocked: {'; '.join(reasons)}. Settlement hold is locked until seller submits a verified correction."

    if outcome == GateOutcome.HOLD:
        hold_reasons = []
        for w in warnings:
            if "CARRIER" in w.invariant_code:
                hold_reasons.append("physical carrier acceptance scan is pending (label created)")
            elif "ETA" in w.invariant_code:
                hold_reasons.append("carrier estimated arrival exceeds promised delivery deadline")
            elif "TRUST" in w.invariant_code:
                hold_reasons.append("awaiting telemetry proof from shipping carrier")
            else:
                hold_reasons.append(w.message)

        if hold_reasons:
            return f"Settlement on hold: {'; '.join(hold_reasons)}."
        return "Settlement on hold awaiting fulfillment progression."

    return "Gate evaluation pending."

