"""Fulfillment Evidence Ingestion Service with automatic gate re-evaluation (FULF-01, DRIFT-02)."""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import canonical_json
from app.core.clock import Clock, SystemClock
from app.core.models import (
    FulfillmentEvidence,
    GateEvaluationRecord,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.drift.engine import evaluate
from app.drift.models import GateEvaluation
from app.fulfillment.models import IngestEvidenceRequest, IngestEvidenceResponse
from app.ledger.events import append_event

logger = logging.getLogger(__name__)


class FulfillmentService:
    """Manages fulfillment evidence deduplication, ledger logging, and gate re-evaluation."""

    def __init__(self, db: Session, clock: Optional[Clock] = None) -> None:
        self.db = db
        self.clock = clock or SystemClock()

    def get_evidence_list(self, purchase_id: str) -> List[FulfillmentEvidence]:
        stmt = (
            select(FulfillmentEvidence)
            .where(FulfillmentEvidence.purchase_id == purchase_id)
            .order_by(FulfillmentEvidence.seq.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_latest_receipt(self, purchase_id: str) -> Optional[PromiseReceipt]:
        stmt = (
            select(PromiseReceipt)
            .where(PromiseReceipt.purchase_id == purchase_id)
            .order_by(PromiseReceipt.version.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def get_latest_authorization(self, purchase_id: str) -> Optional[PaymentAuthorization]:
        stmt = (
            select(PaymentAuthorization)
            .where(PaymentAuthorization.purchase_id == purchase_id)
            .order_by(PaymentAuthorization.created_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalars().first()

    def reevaluate_gate(self, purchase_id: str) -> Optional[GateEvaluation]:
        """Re-evaluate deterministic invariants against all accumulated evidence (DRIFT-02)."""
        receipt = self.get_latest_receipt(purchase_id)
        if not receipt:
            return None

        auth = self.get_latest_authorization(purchase_id)
        evidence_list = self.get_evidence_list(purchase_id)
        now_dt = self.clock.now()

        evaluation = evaluate(
            receipt=receipt,
            auth=auth,
            evidence_list=evidence_list,
            now=now_dt,
        )

        # Record evaluation audit in DB
        eval_record = GateEvaluationRecord(
            purchase_id=purchase_id,
            version=receipt.version,
            outcome=evaluation.outcome.value,
            status_pill=evaluation.status_pill,
            findings_json=canonical_json([f.model_dump() for f in evaluation.findings]),
            explanation=evaluation.explanation,
            evaluated_at=now_dt,
        )
        self.db.add(eval_record)

        # Update purchase status to match gate
        purchase = self.db.get(Purchase, purchase_id)
        if purchase and purchase.status not in ("completed", "cancelled"):
            if evaluation.status_pill == "CAPTURE BLOCKED":
                purchase.status = "capture_blocked"
            elif evaluation.status_pill == "RENEWAL_REQUIRED":
                purchase.status = "renewal_required"
            elif evaluation.status_pill == "HOLD":
                purchase.status = "hold"
            elif evaluation.status_pill == "AUTHORIZED · NOT CAPTURED":
                purchase.status = "authorized"

        # Log GATE_EVALUATED to decision ledger
        append_event(
            session=self.db,
            purchase_id=purchase_id,
            event_type="GATE_EVALUATED",
            actor="drift_engine",
            payload={
                "outcome": evaluation.outcome.value,
                "status_pill": evaluation.status_pill,
                "can_capture": evaluation.can_capture,
                "findings_count": len(evaluation.findings),
            },
            clock=self.clock,
        )

        self.db.commit()
        return evaluation

    def ingest_evidence(self, req: IngestEvidenceRequest) -> IngestEvidenceResponse:
        """Ingest typed fulfillment evidence with deduplication (FULF-01)."""
        purchase = self.db.get(Purchase, req.purchase_id)
        if not purchase:
            raise ValueError(f"Purchase {req.purchase_id} not found")

        # FULF-01: Deduplication check
        dup_stmt = (
            select(FulfillmentEvidence)
            .where(
                FulfillmentEvidence.purchase_id == req.purchase_id,
                FulfillmentEvidence.source == req.source,
                FulfillmentEvidence.external_event_id == req.external_event_id,
            )
            .limit(1)
        )
        existing = self.db.execute(dup_stmt).scalars().first()
        if existing:
            logger.info("Duplicate fulfillment event %s for purchase %s (deduplicated)", req.external_event_id, req.purchase_id)
            gate = self.reevaluate_gate(req.purchase_id)
            return IngestEvidenceResponse(
                status="duplicate",
                evidence_id=existing.id,
                gate=gate,
            )

        # Calculate next sequence number for this purchase
        last_ev_stmt = (
            select(FulfillmentEvidence)
            .where(FulfillmentEvidence.purchase_id == req.purchase_id)
            .order_by(FulfillmentEvidence.seq.desc())
            .limit(1)
        )
        last_ev = self.db.execute(last_ev_stmt).scalars().first()
        next_seq = (last_ev.seq + 1) if last_ev else 1

        now_dt = self.clock.now()
        evidence = FulfillmentEvidence(
            purchase_id=req.purchase_id,
            seq=next_seq,
            source=req.source,
            external_event_id=req.external_event_id,
            trust_level=req.trust_level,
            is_synthetic=req.is_synthetic,
            carrier_status=req.carrier_status,
            sku=req.sku,
            condition=req.condition,
            color=req.color,
            eta=req.eta,
            raw_payload=canonical_json(req.raw_payload or {}),
            recorded_at=now_dt,
        )
        self.db.add(evidence)
        self.db.flush()

        # Log EVIDENCE_INGESTED to ledger
        append_event(
            session=self.db,
            purchase_id=req.purchase_id,
            event_type="EVIDENCE_INGESTED",
            actor="fulfillment_service",
            payload={
                "evidence_id": evidence.id,
                "seq": next_seq,
                "source": req.source,
                "carrier_status": req.carrier_status,
                "sku": req.sku,
                "condition": req.condition,
            },
            clock=self.clock,
        )
        self.db.commit()

        # Re-evaluate gate (DRIFT-02)
        gate = self.reevaluate_gate(req.purchase_id)

        return IngestEvidenceResponse(
            status="ingested",
            evidence_id=evidence.id,
            gate=gate,
        )

