"""Promise Replay timeline service with chain integrity verification (UI-03, LEDG-02)."""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import to_utc_iso
from app.core.models import (
    DecisionEvent,
    FulfillmentEvidence,
    GateEvaluationRecord,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.ledger.verify import verify_chain
from app.proof.counterfactual import counterfactual, gateway_is_simulated
from app.replay.models import ReplayData, ReplayStep

logger = logging.getLogger(__name__)


class ReplayService:
    """Builds 10-step lifecycle replay with divergence detection and ledger chain integrity."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_replay_timeline(self, purchase_id: str) -> ReplayData:
        purchase = self.db.get(Purchase, purchase_id)
        if not purchase:
            raise ValueError(f"Purchase {purchase_id} not found")

        # 1. Cryptographic chain integrity check (LEDG-02)
        chain_intact, chain_count, broken_seq = verify_chain(self.db, purchase_id)

        # 2. Fetch all decision events in chronological sequence
        stmt = (
            select(DecisionEvent)
            .where(DecisionEvent.purchase_id == purchase_id)
            .order_by(DecisionEvent.seq.asc())
        )
        events = list(self.db.execute(stmt).scalars().all())

        # Map events by event_type (preserving all occurrences and latest)
        events_by_type: Dict[str, List[DecisionEvent]] = {}
        for ev in events:
            events_by_type.setdefault(ev.event_type, []).append(ev)

        # 3. Fetch latest gate evaluation record
        gate_stmt = (
            select(GateEvaluationRecord)
            .where(GateEvaluationRecord.purchase_id == purchase_id)
            .order_by(GateEvaluationRecord.evaluated_at.desc())
            .limit(1)
        )
        latest_gate_record = self.db.execute(gate_stmt).scalars().first()

        # Step 1: Buyer Instruction
        step1_ev = (events_by_type.get("INSTRUCTION_SUBMITTED") or events_by_type.get("INSTRUCTION_RECEIVED") or [None])[0]
        step1 = ReplayStep(
            step_number=1,
            name="Buyer Instruction",
            event_type="INSTRUCTION_SUBMITTED",
            status="COMPLETED",
            is_divergence=False,
            timestamp=to_utc_iso(step1_ev.recorded_at) if step1_ev else to_utc_iso(purchase.created_at),
            actor=step1_ev.actor if step1_ev else "buyer",
            payload_summary=json.loads(step1_ev.payload) if step1_ev else {"instruction": purchase.buyer_instruction},
            details=purchase.buyer_instruction,
        )

        # Step 2: Constraints Extracted
        step2_ev = (events_by_type.get("INTENT_EXTRACTED") or [None])[0]
        step2 = ReplayStep(
            step_number=2,
            name="Constraints Extracted",
            event_type="INTENT_EXTRACTED",
            status="COMPLETED" if step2_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step2_ev.recorded_at) if step2_ev else None,
            actor=step2_ev.actor if step2_ev else None,
            payload_summary=json.loads(step2_ev.payload) if step2_ev else None,
            details="Natural language intent parsed into typed budget, condition, and fulfillment constraints" if step2_ev else None,
        )

        # Step 3: Candidate Selected
        step3_ev = (events_by_type.get("PRODUCT_SELECTED") or events_by_type.get("PRODUCT_DISCOVERED") or [None])[0]
        step3 = ReplayStep(
            step_number=3,
            name="Candidate Selected",
            event_type="PRODUCT_SELECTED",
            status="COMPLETED" if step3_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step3_ev.recorded_at) if step3_ev else None,
            actor=step3_ev.actor if step3_ev else None,
            payload_summary=json.loads(step3_ev.payload) if step3_ev else None,
            details="Discovered matching candidate item through Channel3 commerce bridge" if step3_ev else None,
        )

        # Step 4: Quote Confirmed
        step4_ev = (events_by_type.get("QUOTE_CONFIRMED") or [None])[0]
        step4 = ReplayStep(
            step_number=4,
            name="Quote Confirmed",
            event_type="QUOTE_CONFIRMED",
            status="COMPLETED" if step4_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step4_ev.recorded_at) if step4_ev else None,
            actor=step4_ev.actor if step4_ev else None,
            payload_summary=json.loads(step4_ev.payload) if step4_ev else None,
            details="Merchant quote locked with deterministic item, tax, shipping, and total amounts" if step4_ev else None,
        )

        # Step 5: Receipt Compiled & Hashed
        step5_ev = (events_by_type.get("RECEIPT_COMPILED") or [None])[0]
        step5 = ReplayStep(
            step_number=5,
            name="Receipt Compiled & Hashed",
            event_type="RECEIPT_COMPILED",
            status="COMPLETED" if step5_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step5_ev.recorded_at) if step5_ev else None,
            actor=step5_ev.actor if step5_ev else None,
            payload_summary=json.loads(step5_ev.payload) if step5_ev else None,
            details="Canonical RFC 8785 JSON representation hashed into SHA-256 digest" if step5_ev else None,
        )

        # Step 6: Buyer Approved Receipt
        step6_ev = (events_by_type.get("RECEIPT_APPROVED") or [None])[0]
        step6 = ReplayStep(
            step_number=6,
            name="Buyer Approved Receipt",
            event_type="RECEIPT_APPROVED",
            status="COMPLETED" if step6_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step6_ev.recorded_at) if step6_ev else None,
            actor=step6_ev.actor if step6_ev else None,
            payload_summary=json.loads(step6_ev.payload) if step6_ev else None,
            details="Buyer cryptographic authorization of exact promise receipt hash" if step6_ev else None,
        )

        # Step 7: PayPal Hold Authorized
        step7_ev = (events_by_type.get("FUNDS_AUTHORIZED") or [None])[0]
        step7 = ReplayStep(
            step_number=7,
            name="PayPal Hold Authorized",
            event_type="FUNDS_AUTHORIZED",
            status="COMPLETED" if step7_ev else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(step7_ev.recorded_at) if step7_ev else None,
            actor=step7_ev.actor if step7_ev else None,
            payload_summary=json.loads(step7_ev.payload) if step7_ev else None,
            details="Authorization hold placed on buyer payment method with exact receipt custom_id" if step7_ev else None,
        )

        # Step 8: Fulfillment Ingestion
        step8_events = events_by_type.get("EVIDENCE_INGESTED", [])
        latest_ev_event = step8_events[-1] if step8_events else None
        step8 = ReplayStep(
            step_number=8,
            name="Fulfillment Ingestion",
            event_type="EVIDENCE_INGESTED",
            status="COMPLETED" if latest_ev_event else "PENDING",
            is_divergence=False,
            timestamp=to_utc_iso(latest_ev_event.recorded_at) if latest_ev_event else None,
            actor=latest_ev_event.actor if latest_ev_event else None,
            payload_summary=json.loads(latest_ev_event.payload) if latest_ev_event else None,
            details=f"{len(step8_events)} fulfillment event(s) ingested and deduplicated" if step8_events else None,
        )

        # Step 9: Gate Decision (Divergence Highlighted on DRIFT)
        step9_events = events_by_type.get("GATE_EVALUATED", [])
        latest_gate_ev = step9_events[-1] if step9_events else None
        gate_outcome = latest_gate_record.outcome if latest_gate_record else None
        status_pill = latest_gate_record.status_pill if latest_gate_record else None

        step9_status = "PENDING"
        step9_divergence = False
        step9_details = None

        if gate_outcome == "MATCH":
            step9_status = "COMPLETED"
            step9_divergence = False
            step9_details = "All invariants satisfied (Condition, SKU, Finish, Carrier Acceptance, ETA, Auth Valid)."
        elif gate_outcome == "DRIFT":
            step9_status = "DIVERGED"
            step9_divergence = True
            step9_details = latest_gate_record.explanation if latest_gate_record else "Invariant drift detected."
        elif gate_outcome == "PROHIBITED":
            step9_status = "BLOCKED"
            step9_divergence = True
            step9_details = latest_gate_record.explanation if latest_gate_record else "Authorization expired. Renewal required."
        elif gate_outcome == "HOLD":
            step9_status = "HOLD"
            step9_divergence = False
            step9_details = latest_gate_record.explanation if latest_gate_record else "Settlement on hold awaiting fulfillment requirements."

        step9 = ReplayStep(
            step_number=9,
            name="Gate Decision",
            event_type="GATE_EVALUATED",
            status=step9_status,
            is_divergence=step9_divergence,
            timestamp=to_utc_iso(latest_gate_ev.recorded_at) if latest_gate_ev else None,
            actor=latest_gate_ev.actor if latest_gate_ev else None,
            payload_summary=json.loads(latest_gate_ev.payload) if latest_gate_ev else None,
            details=step9_details,
        )

        # Step 10: Settlement Capture / Void
        step10_captured_ev = (events_by_type.get("FUNDS_CAPTURED") or [None])[0]
        step10_voided_ev = (events_by_type.get("AUTHORIZATION_VOIDED") or [None])[0]
        step10_failed_ev = (events_by_type.get("CAPTURE_FAILED") or [None])[0]

        if step10_captured_ev:
            step10 = ReplayStep(
                step_number=10,
                name="Settlement Capture",
                event_type="FUNDS_CAPTURED",
                status="COMPLETED",
                is_divergence=False,
                timestamp=to_utc_iso(step10_captured_ev.recorded_at),
                actor=step10_captured_ev.actor,
                payload_summary=json.loads(step10_captured_ev.payload),
                details="Final settlement capture executed on PayPal.",
            )
        elif step10_voided_ev:
            step10 = ReplayStep(
                step_number=10,
                name="Authorization Voided",
                event_type="AUTHORIZATION_VOIDED",
                status="COMPLETED",
                is_divergence=False,
                timestamp=to_utc_iso(step10_voided_ev.recorded_at),
                actor=step10_voided_ev.actor,
                payload_summary=json.loads(step10_voided_ev.payload),
                details="Held funds released back to buyer.",
            )
        elif step10_failed_ev:
            step10 = ReplayStep(
                step_number=10,
                name="Settlement Capture Failed",
                event_type="CAPTURE_FAILED",
                status="FAILED",
                is_divergence=True,
                timestamp=to_utc_iso(step10_failed_ev.recorded_at),
                actor=step10_failed_ev.actor,
                payload_summary=json.loads(step10_failed_ev.payload),
                details="Capture failed on payment gateway.",
            )
        elif gate_outcome == "DRIFT":
            step10 = ReplayStep(
                step_number=10,
                name="Settlement Blocked",
                event_type="CAPTURE_BLOCKED",
                status="BLOCKED",
                is_divergence=False,
                details="Settlement capture strictly blocked by Invariant Drift Gate.",
            )
        elif gate_outcome == "PROHIBITED":
            step10 = ReplayStep(
                step_number=10,
                name="Settlement Prohibited",
                event_type="CAPTURE_PROHIBITED",
                status="BLOCKED",
                is_divergence=False,
                details="Settlement prohibited due to expired authorization honor period.",
            )
        elif gate_outcome == "HOLD":
            step10 = ReplayStep(
                step_number=10,
                name="Settlement on Hold",
                event_type="CAPTURE_HOLD",
                status="HOLD",
                is_divergence=False,
                details="Settlement paused until carrier acceptance / ETA requirements met.",
            )
        else:
            step10 = ReplayStep(
                step_number=10,
                name="Settlement Capture",
                event_type="FUNDS_CAPTURED",
                status="PENDING",
                is_divergence=False,
                details="Awaiting settlement execution.",
            )

        all_steps = [step1, step2, step3, step4, step5, step6, step7, step8, step9, step10]

        # Determine divergence
        is_diverged = any(s.is_divergence for s in all_steps)
        divergence_step = next((s.step_number for s in all_steps if s.is_divergence), None)

        # Determine current step
        active_step = 1
        for s in all_steps:
            if s.status in ("COMPLETED", "DIVERGED", "BLOCKED", "FAILED"):
                active_step = s.step_number

        auth = self.db.execute(
            select(PaymentAuthorization).where(PaymentAuthorization.purchase_id == purchase_id)
        ).scalars().first()
        has_ev = self.db.execute(
            select(FulfillmentEvidence.id).where(FulfillmentEvidence.purchase_id == purchase_id).limit(1)
        ).first() is not None
        amount = auth.amount_cents if auth else 0
        cf = {
            **counterfactual(amount, has_ev, amount if auth and auth.state == "captured" else 0),
            "simulated": gateway_is_simulated(),
        }

        return ReplayData(
            purchase_id=purchase_id,
            steps=all_steps,
            current_step=active_step,
            is_diverged=is_diverged,
            divergence_step=divergence_step,
            chain_intact=chain_intact,
            chain_event_count=chain_count,
            broken_step=broken_seq,
            gate_outcome=gate_outcome,
            status_pill=status_pill,
            counterfactual=cf,
        )

