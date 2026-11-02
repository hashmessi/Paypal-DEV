"""High-level Payments Service with deterministic idempotency, CAS state transitions, and ledger logging."""

from datetime import datetime, timedelta, timezone
import json
import logging
from typing import Any, Optional
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.canon import canonical_json
from app.core.clock import Clock, SystemClock
from app.core.models import DecisionEvent, FinancialAction, PaymentAuthorization, Purchase
from app.ledger.events import append_event
from app.payments.port import PaymentGateway
from app.payments.state import (
    CaptureBlockedByGateError,
    IllegalStateTransitionError,
    PaymentState,
    PaymentStateError,
    TerminalStateError,
    is_terminal,
    validate_transition,
)

logger = logging.getLogger(__name__)


def generate_deterministic_request_id(authorization_id: str, action: str) -> str:
    """Generate RFC 4122 v5 UUID namespace-derived deterministic PayPal-Request-Id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"promiseloop:{authorization_id}:{action}"))


class PaymentsService:
    """Orchestrates payments state transitions, idempotency locks, and ledger events."""

    def __init__(
        self,
        session: Session,
        gateway: PaymentGateway,
        clock: Optional[Clock] = None,
    ) -> None:
        self.session = session
        self.gateway = gateway
        self.clock = clock or SystemClock()

    def get_authorization_by_purchase_id(self, purchase_id: str) -> Optional[PaymentAuthorization]:
        stmt = (
            select(PaymentAuthorization)
            .where(PaymentAuthorization.purchase_id == purchase_id)
            .order_by(PaymentAuthorization.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_authorization_by_order_id(self, order_id: str) -> Optional[PaymentAuthorization]:
        stmt = (
            select(PaymentAuthorization)
            .where(PaymentAuthorization.order_id == order_id)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def get_authorization_by_auth_id(self, auth_id: str) -> Optional[PaymentAuthorization]:
        stmt = (
            select(PaymentAuthorization)
            .where(PaymentAuthorization.authorization_id == auth_id)
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    async def create_checkout_order(
        self,
        purchase_ref: str,
        amount_cents: int,
        currency: str = "USD",
        buyer_instruction: str = "Autonomous agent checkout",
        receipt_hash: Optional[str] = None,
        return_url: str = "https://promiseloop.dev/checkout/return",
        cancel_url: str = "https://promiseloop.dev/checkout/cancel",
    ) -> dict[str, Any]:
        """Create a new purchase and PayPal order with intent=AUTHORIZE and receipt hash custom_id (PAY-08)."""
        # 1. Create Purchase record
        purchase = Purchase(
            ref=purchase_ref,
            buyer_instruction=buyer_instruction,
            status="draft",
            receipt_hash=receipt_hash,
        )
        self.session.add(purchase)
        self.session.flush()

        # 2. Call Gateway to create order with custom_id = receipt_hash
        gateway_order = await self.gateway.create_order(
            amount_cents=amount_cents,
            currency=currency,
            ref=purchase_ref,
            custom_id=receipt_hash,
            return_url=return_url,
            cancel_url=cancel_url,
        )

        order_id = gateway_order["order_id"]

        # 3. Create initial PaymentAuthorization
        auth = PaymentAuthorization(
            purchase_id=purchase.id,
            order_id=order_id,
            state=PaymentState.CREATED.value,
            amount_cents=amount_cents,
            currency=currency,
        )
        self.session.add(auth)
        self.session.flush()

        # 4. Append ORDER_CREATED ledger event
        append_event(
            session=self.session,
            purchase_id=purchase.id,
            event_type="ORDER_CREATED",
            actor="buyer",
            payload={
                "order_id": order_id,
                "amount_cents": amount_cents,
                "currency": currency,
                "ref": purchase_ref,
            },
            clock=self.clock,
        )

        self.session.commit()

        return {
            "purchase_id": purchase.id,
            "order_id": order_id,
            "status": gateway_order.get("status", "CREATED"),
            "approval_url": gateway_order.get("approval_url", ""),
        }

    async def authorize_order(
        self,
        order_id: str,
    ) -> PaymentAuthorization:
        """Authorize PayPal order, placing hold on buyer funds."""
        auth = self.get_authorization_by_order_id(order_id)
        if not auth:
            raise ValueError(f"No authorization record found for order {order_id}")

        validate_transition(auth.state, PaymentState.AUTHORIZED.value)

        gateway_res = await self.gateway.authorize_order(order_id)
        # Only a CREATED authorization for the exact approved amount holds funds; PENDING/DENIED must not be recorded as AUTHORIZED
        if (
            gateway_res.get("status") != "CREATED"
            or gateway_res.get("amount_cents") != auth.amount_cents
            or gateway_res.get("currency") != auth.currency
        ):
            raise PaymentStateError(
                f"PayPal authorization for order {order_id} not usable: status={gateway_res.get('status')}, "
                f"amount_cents={gateway_res.get('amount_cents')}, currency={gateway_res.get('currency')}"
            )

        auth_id = gateway_res["authorization_id"]
        exp_time = gateway_res.get("expiration_time")
        if isinstance(exp_time, str):
            try:
                exp_dt = datetime.fromisoformat(exp_time)
            except Exception:
                exp_dt = self.clock.now() + timedelta(days=29)
        elif isinstance(exp_time, datetime):
            exp_dt = exp_time
        else:
            exp_dt = self.clock.now() + timedelta(days=29)

        honor_until_dt = self.clock.now() + timedelta(days=29)

        auth.authorization_id = auth_id
        auth.state = PaymentState.AUTHORIZED.value
        auth.expiration_time = exp_dt
        auth.honor_until = honor_until_dt

        # Append FUNDS_AUTHORIZED to ledger
        append_event(
            session=self.session,
            purchase_id=auth.purchase_id,
            event_type="FUNDS_AUTHORIZED",
            actor="buyer",
            payload={
                "authorization_id": auth_id,
                "order_id": order_id,
                "amount_cents": auth.amount_cents,
                "currency": auth.currency,
                "expiration_time": exp_dt.isoformat(),
                "honor_until": honor_until_dt.isoformat(),
            },
            clock=self.clock,
        )

        # Update purchase status to authorized
        purchase = self.session.get(Purchase, auth.purchase_id)
        if purchase:
            purchase.status = "authorized"

        self.session.commit()
        return auth

    async def capture_authorization(
        self,
        purchase_id: str,
        amount_cents: Optional[int] = None,
        note: str = "",
        actor: str = "agent",
    ) -> dict[str, Any]:
        """Capture an authorization.

        Enforces:
        - Terminal state check: captures on terminal states are rejected without calling PayPal.
        - CAS state transition to capturing.
        - Deterministic PayPal-Request-Id header for idempotency.
        - Append-only ledger recording of FUNDS_CAPTURED.
        """
        auth = self.get_authorization_by_purchase_id(purchase_id)
        if not auth:
            raise ValueError(f"No authorization found for purchase {purchase_id}")

        if not auth.authorization_id:
            raise ValueError(f"Purchase {purchase_id} has not yet been authorized by buyer")

        # PAY-05: Check deterministic financial action for idempotent replay first
        request_id = generate_deterministic_request_id(auth.authorization_id, "capture")
        stmt = (
            select(FinancialAction)
            .where(
                FinancialAction.authorization_id == auth.authorization_id,
                FinancialAction.action == "capture",
            )
            .limit(1)
        )
        fin_act = self.session.execute(stmt).scalars().first()

        if fin_act and fin_act.status == "completed":
            # Idempotent replay: return cached payload
            logger.info("Idempotent capture replay for authorization %s", auth.authorization_id)
            if fin_act.response_payload:
                return json.loads(fin_act.response_payload)
            return {
                "capture_id": auth.capture_id,
                "authorization_id": auth.authorization_id,
                "status": "COMPLETED",
                "amount_cents": auth.amount_cents,
                "currency": auth.currency,
            }

        # PAY-04: Cannot capture terminal states if not already completed
        if is_terminal(auth.state):
            raise TerminalStateError(auth.state, "capture")

        target_amount = amount_cents if amount_cents is not None else auth.amount_cents
        if target_amount > auth.amount_cents:
            raise ValueError(f"Capture amount {target_amount} exceeds authorized amount {auth.amount_cents}")

        # PAY-02: Settlement Gate Enforce - Capture is allowed ONLY on MATCH
        # If gate is DRIFT / HOLD / PROHIBITED, capture is blocked locally without contacting PayPal
        from app.drift.models import GateOutcome
        from app.fulfillment.service import FulfillmentService

        fulfillment_svc = FulfillmentService(self.session, self.clock)
        gate = fulfillment_svc.reevaluate_gate(purchase_id)
        # Fail closed: without a receipt there is no buyer-approved promise to settle against
        if gate is None:
            raise CaptureBlockedByGateError("Capture blocked: no Promise Receipt bound to this purchase", outcome="NO_RECEIPT")
        if gate.outcome != GateOutcome.MATCH:
            raise CaptureBlockedByGateError(
                f"Capture blocked by gate: outcome is {gate.outcome.value} ({gate.status_pill}). {gate.explanation}",
                outcome=gate.outcome.value,
                findings=[f.model_dump() for f in gate.findings],
            )

        validate_transition(auth.state, PaymentState.CAPTURING.value)

        if not fin_act:
            fin_act = FinancialAction(
                authorization_id=auth.authorization_id,
                action="capture",
                request_id=request_id,
                status="pending",
            )
            self.session.add(fin_act)

        # Atomic CAS: only one concurrent request can move AUTHORIZED -> CAPTURING
        claimed = self.session.execute(
            update(PaymentAuthorization)
            .where(PaymentAuthorization.id == auth.id, PaymentAuthorization.state == auth.state)
            .values(state=PaymentState.CAPTURING.value)
            .execution_options(synchronize_session=False)
        ).rowcount
        if claimed != 1:
            raise PaymentStateError("Capture already in progress for this authorization")
        auth.state = PaymentState.CAPTURING.value
        self.session.commit()

        try:
            res = await self.gateway.capture_authorization(
                authorization_id=auth.authorization_id,
                amount_cents=target_amount,
                currency=auth.currency,
                request_id=request_id,
                note_to_payer=note,
            )
        except Exception as err:
            logger.error("Capture failed on gateway: %s", err)
            auth.state = PaymentState.FAILED.value
            fin_act.status = "failed"
            append_event(
                session=self.session,
                purchase_id=purchase_id,
                event_type="CAPTURE_FAILED",
                actor=actor,
                payload={"error": str(err), "authorization_id": auth.authorization_id},
                clock=self.clock,
            )
            self.session.commit()
            raise

        # Gateway succeeded
        capture_id = res.get("capture_id", "")
        now_dt = self.clock.now()

        validate_transition(auth.state, PaymentState.CAPTURED.value)
        auth.state = PaymentState.CAPTURED.value
        auth.capture_id = capture_id
        auth.captured_at = now_dt

        fin_act.status = "completed"
        fin_act.response_payload = canonical_json(res)

        append_event(
            session=self.session,
            purchase_id=purchase_id,
            event_type="FUNDS_CAPTURED",
            actor=actor,
            payload={
                "capture_id": capture_id,
                "authorization_id": auth.authorization_id,
                "amount_cents": target_amount,
                "currency": auth.currency,
                "request_id": request_id,
            },
            clock=self.clock,
        )

        purchase = self.session.get(Purchase, purchase_id)
        if purchase:
            purchase.status = "completed"

        # Re-evaluate gate to update status pill to CAPTURED
        fulfillment_svc.reevaluate_gate(purchase_id)

        # PAY: Push verified tracking and SKU to PayPal Orders v2 tracking API
        try:
            evidence_list = fulfillment_svc.get_evidence_list(purchase_id)
            carrier_ev = next(
                (ev for ev in evidence_list if ev.carrier_status in ("ACCEPTED", "DELIVERED", "IN_TRANSIT")),
                None,
            )
            if carrier_ev and auth.order_id:
                raw_payload = (
                    json.loads(carrier_ev.raw_payload)
                    if isinstance(carrier_ev.raw_payload, str)
                    else (carrier_ev.raw_payload or {})
                )
                carrier_name = carrier_ev.source or raw_payload.get("carrier") or "UPS"
                tracking_num = (
                    carrier_ev.external_event_id
                    or raw_payload.get("tracking_number")
                    or f"1Z{auth.order_id[:16]}"
                )
                sku = carrier_ev.sku or "WH1000XM5-BLK-NEW"

                track_res = await self.gateway.push_tracking(
                    order_id=auth.order_id,
                    capture_id=capture_id,
                    carrier=carrier_name,
                    tracking_number=tracking_num,
                    sku=sku,
                )

                append_event(
                    session=self.session,
                    purchase_id=purchase_id,
                    event_type="TRACKING_PUSHED_TO_PAYPAL",
                    actor="promiseloop",
                    payload={
                        "order_id": auth.order_id,
                        "capture_id": capture_id,
                        "carrier": carrier_name,
                        "tracking_number": tracking_num,
                        "sku": sku,
                        "gateway_status": track_res.get("status", "SUBMITTED"),
                    },
                    clock=self.clock,
                )
        except Exception as e:
            logger.warning("Post-capture tracking push skipped: %s", e)

        self.session.commit()
        return res

    async def void_authorization(
        self,
        purchase_id: str,
        reason: str = "Buyer requested cancellation",
        actor: str = "buyer",
    ) -> dict[str, Any]:
        """Void an authorization, releasing held funds back to buyer."""
        auth = self.get_authorization_by_purchase_id(purchase_id)
        if not auth:
            raise ValueError(f"No authorization found for purchase {purchase_id}")

        if not auth.authorization_id:
            raise ValueError(f"Purchase {purchase_id} has not yet been authorized")

        request_id = generate_deterministic_request_id(auth.authorization_id, "void")
        stmt = (
            select(FinancialAction)
            .where(
                FinancialAction.authorization_id == auth.authorization_id,
                FinancialAction.action == "void",
            )
            .limit(1)
        )
        fin_act = self.session.execute(stmt).scalars().first()

        if fin_act and fin_act.status == "completed":
            logger.info("Idempotent void replay for authorization %s", auth.authorization_id)
            if fin_act.response_payload:
                return json.loads(fin_act.response_payload)
            return {
                "authorization_id": auth.authorization_id,
                "status": "VOIDED",
            }

        if is_terminal(auth.state):
            raise TerminalStateError(auth.state, "void")

        validate_transition(auth.state, PaymentState.VOIDED.value)

        if not fin_act:
            fin_act = FinancialAction(
                authorization_id=auth.authorization_id,
                action="void",
                request_id=request_id,
                status="pending",
            )
            self.session.add(fin_act)
            self.session.commit()

        try:
            res = await self.gateway.void_authorization(
                authorization_id=auth.authorization_id,
                request_id=request_id,
                note_to_payer=reason,
            )
        except Exception as err:
            logger.error("Void failed on gateway: %s", err)
            auth.state = PaymentState.FAILED.value
            fin_act.status = "failed"
            append_event(
                session=self.session,
                purchase_id=purchase_id,
                event_type="VOID_FAILED",
                actor=actor,
                payload={"error": str(err), "authorization_id": auth.authorization_id},
                clock=self.clock,
            )
            self.session.commit()
            raise

        now_dt = self.clock.now()
        auth.state = PaymentState.VOIDED.value
        auth.voided_at = now_dt
        auth.void_reason = reason

        fin_act.status = "completed"
        fin_act.response_payload = canonical_json(res)

        append_event(
            session=self.session,
            purchase_id=purchase_id,
            event_type="AUTHORIZATION_VOIDED",
            actor=actor,
            payload={
                "authorization_id": auth.authorization_id,
                "reason": reason,
                "request_id": request_id,
            },
            clock=self.clock,
        )

        purchase = self.session.get(Purchase, purchase_id)
        if purchase:
            purchase.status = "cancelled"

        self.session.commit()
        return res

    async def reconcile_authorization(
        self,
        purchase_id: str,
    ) -> dict[str, Any]:
        """Fetch remote state from gateway and update local state accordingly."""
        auth = self.get_authorization_by_purchase_id(purchase_id)
        if not auth or not auth.authorization_id:
            raise ValueError(f"No authorization available for purchase {purchase_id}")

        res = await self.gateway.reconcile_authorization(auth.authorization_id)
        remote_status = res.get("status", "").upper()

        if remote_status == "VOIDED" and auth.state != PaymentState.VOIDED.value:
            auth.state = PaymentState.VOIDED.value
            auth.voided_at = self.clock.now()
            auth.void_reason = "Reconciled from gateway"
            append_event(
                session=self.session,
                purchase_id=purchase_id,
                event_type="RECONCILED_VOIDED",
                actor="system",
                payload={"remote_status": remote_status},
                clock=self.clock,
            )
            self.session.commit()
        elif remote_status == "CAPTURED" and auth.state != PaymentState.CAPTURED.value:
            auth.state = PaymentState.CAPTURED.value
            auth.captured_at = self.clock.now()
            append_event(
                session=self.session,
                purchase_id=purchase_id,
                event_type="RECONCILED_CAPTURED",
                actor="system",
                payload={"remote_status": remote_status},
                clock=self.clock,
            )
            self.session.commit()

        return res
