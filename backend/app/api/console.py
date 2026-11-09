"""Merchant Control Tower, Proof and Events read APIs + fresh demo run (UI-04, PROOF-02, DEPLOY-03)."""

import json
from datetime import timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_clock, get_gateway
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import (
    DecisionEvent,
    FulfillmentEvidence,
    GateEvaluationRecord,
    PaymentAuthorization,
    PromiseReceipt,
    Purchase,
)
from app.payments.port import PaymentGateway
from app.payments.service import PaymentsService
from app.proof.counterfactual import counterfactual, gateway_is_simulated
from app.proof.runner import run_proof
from app.receipt.compiler import compile_canonical_receipt
from app.receipt.service import ReceiptService

router = APIRouter(tags=["console"])

_INVARIANT = {"INV-01": "product", "INV-02": "product", "INV-03": "evidence", "INV-04": "promise", "INV-05": "evidence", "INV-06": "financial"}
_SEVERITY = {"BLOCKER": "DRIFT", "WARNING": "HOLD", "INFO": "INFO"}
_OPEN = {"created", "approved", "authorized"}


def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None


def _json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        return {}


def _decision(g: Optional[GateEvaluationRecord], receipt_hash: str) -> Optional[Dict[str, Any]]:
    if not g:
        return None
    findings = [
        {
            "code": f.get("invariant_code", ""),
            "invariant": _INVARIANT.get(f.get("invariant_code", "")[:6], "decision"),
            "severity": _SEVERITY.get(str(f.get("severity", "")).upper().split(".")[-1], "INFO"),
            "expected": f.get("expected"),
            "observed": f.get("actual"),
            "title": f.get("message", ""),
            "explanation": f.get("message", ""),
            "evidence_ids": [f["evidence_id"]] if f.get("evidence_id") else [],
        }
        for f in _json_list(g.findings_json)
    ]
    return {
        "outcome": g.outcome,
        "findings": findings,
        "receipt_hash": receipt_hash,
        "evaluated_at": _iso(g.evaluated_at),
        "rules_version": "invariants-v1",
    }


def _json_list(s: str) -> List[Dict[str, Any]]:
    try:
        v = json.loads(s)
    except Exception:
        return []
    return [f for f in v if isinstance(f, dict)] if isinstance(v, list) else []


def _promise(db: Session, p: Purchase) -> Dict[str, Any]:
    r = db.execute(select(PromiseReceipt).where(PromiseReceipt.purchase_id == p.id).order_by(PromiseReceipt.version.desc()).limit(1)).scalars().first()
    a = db.execute(select(PaymentAuthorization).where(PaymentAuthorization.purchase_id == p.id)).scalars().first()
    g = db.execute(select(GateEvaluationRecord).where(GateEvaluationRecord.purchase_id == p.id).order_by(GateEvaluationRecord.evaluated_at.desc()).limit(1)).scalars().first()
    ev = db.execute(select(FulfillmentEvidence).where(FulfillmentEvidence.purchase_id == p.id).order_by(FulfillmentEvidence.seq)).scalars().all()
    amount = a.amount_cents if a else 0
    cf = counterfactual(amount, bool(ev), amount if a and a.state == "captured" else 0)
    snap, quote, cons = (_json(r.product_snapshot_json), _json(r.merchant_quote_json), _json(r.constraints_json)) if r else ({}, {}, {})
    return {
        "id": p.id,
        "ref": p.ref,
        "version": r.version if r else p.version,
        "status": r.status if r else "draft",
        "buyer_instruction": p.buyer_instruction,
        "instruction_source": "fallback",
        "constraints": cons,
        "product_snapshot": snap,
        "merchant_quote": quote,
        "receipt_hash": r.receipt_hash if r else "",
        "approved_at": _iso(r.approved_at) if r else None,
        "payment": {
            "order_id": a.order_id if a else None,
            "authorization_id": a.authorization_id if a else None,
            "capture_id": a.capture_id if a else None,
            "state": a.state if a else "created",
            "amount_cents": a.amount_cents if a else 0,
            "currency": a.currency if a else "USD",
            "expiration_time": _iso(a.expiration_time) if a else None,
            "honor_until": _iso(a.honor_until) if a else None,
            "captured_at": _iso(a.captured_at) if a else None,
            "voided_at": _iso(a.voided_at) if a else None,
            "void_reason": a.void_reason if a else None,
            "is_simulated": gateway_is_simulated(),
            "updated_at": _iso(a.updated_at) if a else _iso(p.updated_at),
        },
        "gate_decision": _decision(g, r.receipt_hash if r else ""),
        "evidence_events": [
            {
                "id": e.id, "seq": e.seq, "source": e.source,
                "source_type": "carrier" if e.trust_level == "CARRIER_TELEMETRY" else "claim",
                "synthetic": e.is_synthetic, "event_type": e.carrier_status or "EVIDENCE",
                "occurred_at": _iso(e.recorded_at), "recorded_at": _iso(e.recorded_at),
                "status_display": e.carrier_status or "", "payload": _json(e.raw_payload),
            }
            for e in ev
        ],
        "counterfactual": {**cf, "simulated": gateway_is_simulated()},
        "lifecycle": [],
        "created_at": _iso(p.created_at),
        "updated_at": _iso(p.updated_at),
    }


@router.get("/tower")
async def tower(db: Session = Depends(get_db)):
    purchases = db.execute(select(Purchase).order_by(Purchase.created_at.desc()).limit(200)).scalars().all()
    promises = [_promise(db, p) for p in purchases]
    held = [x for x in promises if x["payment"]["state"] == "authorized"]
    review = [x for x in promises if x["gate_decision"] and x["gate_decision"]["outcome"] in ("DRIFT", "HOLD", "PROHIBITED")]
    judged = [x for x in promises if x["gate_decision"]]
    matched = [x for x in judged if x["gate_decision"]["outcome"] == "MATCH"]
    return {
        "kpis": {
            "active_promises": sum(x["payment"]["state"] in _OPEN for x in promises),
            "verified_outcomes_pct": round(100 * len(matched) / len(judged)) if judged else 0,
            "review_required": len(review),
            "authorized_not_captured_cents": sum(x["payment"]["amount_cents"] for x in held),
            "authorized_not_captured_count": len(held),
            "loss_avoided_cents": sum(x["counterfactual"]["loss_avoided_cents"] for x in promises),
            "loss_avoided_simulated": gateway_is_simulated(),
        },
        "promises": promises,
        "openDriftCount": len(review),
    }


@router.get("/promises/{purchase_id}")
async def promise(purchase_id: str, db: Session = Depends(get_db)):
    p = db.get(Purchase, purchase_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Purchase {purchase_id} not found")
    return _promise(db, p)


@router.get("/events")
async def events(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = db.execute(select(DecisionEvent, Purchase.ref).join(Purchase, Purchase.id == DecisionEvent.purchase_id).order_by(DecisionEvent.recorded_at.desc(), DecisionEvent.seq.desc()).limit(100)).all()
    bad = ("BLOCK", "DRIFT", "VOID", "EXPIRED", "FAILED")
    return [
        {
            "seq": e.seq, "purchase_id": e.purchase_id, "purchase_ref": ref, "type": e.event_type,
            "source": e.actor, "actor": e.actor, "recorded_at": _iso(e.recorded_at),
            "payload_summary": e.payload[:140], "hash": e.event_hash,
            "status_pill": {"label": e.event_type.replace("_", " "), "tone": "bad" if any(b in e.event_type for b in bad) else "info"},
        }
        for e, ref in rows
    ]


@lru_cache(maxsize=1)
def _proof_cached() -> Dict[str, Any]:
    return run_proof()  # deterministic: fixed clock + fixed scenarios


@router.get("/proof")
def proof():  # sync on purpose: run_proof() calls asyncio.run(), illegal inside the event loop
    return _proof_cached()


class DemoRunRequest(BaseModel):
    instruction: Optional[str] = None


@router.post("/demo/run")
async def run_demo(
    req: DemoRunRequest,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """DEPLOY-03: fresh purchase, approved receipt and authorization every call; all dates relative to the clock."""
    now = clock.now()
    constraints = {
        "product_type": "over-ear headphones", "condition": "new", "color": "black",
        "max_total_cents": 10000, "currency": "USD", "deliver_within_days": 5,
        "resolved_deadline_at": (now + timedelta(days=5)).isoformat(),
    }
    snapshot = {"title": "Sony WH-1000XM5 (black)", "sku": "WH1000XM5-BLK-NEW", "color": "black", "condition": "new"}
    quote = {"total_cents": 8999, "currency": "USD", "sku": "WH1000XM5-BLK-NEW", "promised_delivery_at": (now + timedelta(days=4)).isoformat()}
    _, receipt_hash, _ = compile_canonical_receipt(constraints, snapshot, quote, version=1)

    svc = PaymentsService(session=db, gateway=gateway, clock=clock)
    ref = f"PL-{int(now.timestamp()) % 1000000:06d}"
    order = await svc.create_checkout_order(
        purchase_ref=ref, amount_cents=quote["total_cents"], currency="USD",
        buyer_instruction=req.instruction or "New black over-ear headphones under $100, arrive within 5 days",
        receipt_hash=receipt_hash,
    )
    pid = order["purchase_id"]
    rs = ReceiptService(db=db, clock=clock)
    rs.compile_receipt(pid, constraints, snapshot, quote)
    rs.approve_receipt(pid, receipt_hash)
    await svc.authorize_order(order_id=order["order_id"])
    return {"purchase_id": pid, "ref": ref}
