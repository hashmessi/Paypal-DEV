"""Demo scenarios endpoint for evaluator testing without manual PayPal dashboard clicks."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_clock, get_gateway
from app.api.guards import require_admin
from app.core.clock import Clock
from app.core.db import get_db
from app.core.models import DecisionEvent, PaymentAuthorization, Purchase
from app.ledger.events import append_event
from app.payments.port import PaymentGateway
from app.payments.service import PaymentsService
from app.payments.state import PaymentState

router = APIRouter(prefix="/demo", tags=["demo"])


class ScenarioRequest(BaseModel):
    scenario: str = Field(
        ...,
        description="Scenario type: 'happy_path' | 'expired_auth' | 'cancelled_auth' | 'tampered_ledger'",
        json_schema_extra={"example": "happy_path"},
    )
    ref: Optional[str] = Field(None, description="Optional custom reference")
    amount_cents: int = Field(default=8999, description="Amount in minor cents", ge=1)


@router.post("/scenarios", dependencies=[Depends(require_admin)])
async def seed_demo_scenario(
    req: ScenarioRequest,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Seed a deterministic test scenario with clock-relative dates and authorizations."""
    service = PaymentsService(session=db, gateway=gateway, clock=clock)
    now_dt = clock.now()
    ref = req.ref or f"DEMO-{req.scenario.upper()[:8]}-{int(now_dt.timestamp())}"

    # 1. Create order
    order_res = await service.create_checkout_order(
        purchase_ref=ref,
        amount_cents=req.amount_cents,
        currency="USD",
        buyer_instruction=f"Demo scenario: {req.scenario}",
    )
    purchase_id = order_res["purchase_id"]
    order_id = order_res["order_id"]

    # 2. Authorize
    auth = await service.authorize_order(order_id=order_id)

    # 3. Apply scenario modifications
    if req.scenario == "happy_path":
        return {
            "scenario": req.scenario,
            "purchase_id": purchase_id,
            "order_id": order_id,
            "authorization_id": auth.authorization_id,
            "state": auth.state,
            "amount_cents": auth.amount_cents,
            "message": "Authorized and ready for agent promise verification or capture.",
        }

    elif req.scenario == "expired_auth":
        # Force expiration into the past
        past_dt = now_dt - timedelta(days=2)
        auth.expiration_time = past_dt
        auth.honor_until = past_dt
        auth.state = PaymentState.EXPIRED.value
        append_event(
            session=db,
            purchase_id=purchase_id,
            event_type="AUTHORIZATION_EXPIRED",
            actor="system",
            payload={"expired_at": past_dt.isoformat()},
            clock=clock,
        )
        db.commit()
        return {
            "scenario": req.scenario,
            "purchase_id": purchase_id,
            "order_id": order_id,
            "authorization_id": auth.authorization_id,
            "state": auth.state,
            "message": "Simulated expired authorization. Capture attempts will be rejected.",
        }

    elif req.scenario == "cancelled_auth":
        await service.void_authorization(
            purchase_id=purchase_id,
            reason="Buyer revoked authorization prior to delivery",
            actor="buyer",
        )
        return {
            "scenario": req.scenario,
            "purchase_id": purchase_id,
            "order_id": order_id,
            "authorization_id": auth.authorization_id,
            "state": auth.state,
            "message": "Authorization voided. Held funds released back to buyer.",
        }

    elif req.scenario == "tampered_ledger":
        # Corrupt the payload of an event to demonstrate cryptographic detection
        last_event = (
            db.query(DecisionEvent)
            .filter(DecisionEvent.purchase_id == purchase_id)
            .order_by(DecisionEvent.seq.desc())
            .first()
        )
        if last_event:
            # Direct SQLite update to bypass standard method
            last_event.payload = '{"tampered":true,"malicious_amount":999999}'
            db.commit()
        return {
            "scenario": req.scenario,
            "purchase_id": purchase_id,
            "message": "Ledger intentionally tampered. Chain verification should fail.",
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown demo scenario: {req.scenario}",
        )
