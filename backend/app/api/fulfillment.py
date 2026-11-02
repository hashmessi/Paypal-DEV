"""Fulfillment telemetry ingestion and scenario console endpoints (FULF-01, FULF-02)."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import FulfillmentEvidence, Purchase
from app.fulfillment.models import IngestEvidenceRequest, IngestEvidenceResponse
from app.fulfillment.scenarios import ScenarioRunner
from app.fulfillment.service import FulfillmentService

router = APIRouter(tags=["fulfillment"])


class TriggerScenarioRequest(BaseModel):
    scenario: str = Field(
        ...,
        description=(
            "Scenario Console trigger key: 'refurbished' | 'wrong_color' | 'corrected' | "
            "'label_only' | 'late_eta' | 'duplicate_event' | 'price_change' | 'advance_clock'"
        ),
    )


@router.post("/fulfillment/evidence", response_model=IngestEvidenceResponse)
async def ingest_evidence(
    req: IngestEvidenceRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Ingest typed fulfillment evidence with deduplication (FULF-01).

    Re-evaluates Invariant Drift Gate and logs EVIDENCE_INGESTED and GATE_EVALUATED events.
    """
    service = FulfillmentService(db=db, clock=clock)
    try:
        return service.ingest_evidence(req)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.post("/fulfillment/scenarios/{purchase_id}")
async def trigger_scenario(
    purchase_id: str,
    req: TriggerScenarioRequest,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Trigger one of 8 Scenario Console actions for judges and testing (FULF-02)."""
    runner = ScenarioRunner(db=db, clock=clock)
    try:
        return runner.trigger_scenario(purchase_id=purchase_id, scenario_key=req.scenario)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.get("/purchases/{purchase_id}/evidence")
async def get_purchase_evidence(
    purchase_id: str,
    db: Session = Depends(get_db),
    clock: Clock = Depends(get_clock),
):
    """Retrieve all ingested fulfillment evidence records for a purchase."""
    purchase = db.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Purchase {purchase_id} not found")

    service = FulfillmentService(db=db, clock=clock)
    evidence_list = service.get_evidence_list(purchase_id)
    return [
        {
            "id": ev.id,
            "seq": ev.seq,
            "source": ev.source,
            "external_event_id": ev.external_event_id,
            "trust_level": ev.trust_level,
            "is_synthetic": ev.is_synthetic,
            "carrier_status": ev.carrier_status,
            "sku": ev.sku,
            "condition": ev.condition,
            "color": ev.color,
            "eta": ev.eta.isoformat() if ev.eta else None,
            "raw_payload": ev.raw_payload,
            "recorded_at": ev.recorded_at.isoformat() if ev.recorded_at else None,
        }
        for ev in evidence_list
    ]

