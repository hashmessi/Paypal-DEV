"""Webhook Event Processor with deduplication and ledger recording."""

import json
import logging
from typing import Any, Mapping, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.canon import canonical_json
from app.core.clock import Clock, SystemClock
from app.core.models import PaymentAuthorization, WebhookEvent
from app.ledger.events import append_event
from app.payments.state import PaymentState, is_terminal

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Processes incoming PayPal webhook events with deduplication and state reconciliation."""

    def __init__(self, session: Session, clock: Optional[Clock] = None) -> None:
        self.session = session
        self.clock = clock or SystemClock()

    def is_duplicate(self, event_id: str) -> bool:
        stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id).limit(1)
        return self.session.execute(stmt).scalars().first() is not None

    async def process_event(
        self,
        headers: Mapping[str, str],
        raw_body: str,
        verified: bool = True,
    ) -> dict[str, Any]:
        """Process webhook notification.

        Idempotent: Duplicate event_ids are safely acknowledged without re-processing.
        Ledger: Appends WEBHOOK_RECEIVED event to the affected purchase ledger.
        Invariants: Never triggers an automatic capture.
        """
        payload = json.loads(raw_body)
        event_id = payload.get("id", "")
        event_type = payload.get("event_type", "UNKNOWN")
        resource = payload.get("resource", {})
        resource_id = resource.get("id", "")

        if not event_id:
            raise ValueError("Malformed webhook event: missing 'id'")

        # PAY-06: Deduplication check
        if self.is_duplicate(event_id):
            logger.info("Webhook %s already processed (deduplicated)", event_id)
            return {"status": "duplicate", "event_id": event_id}

        # Record webhook event
        wh_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            resource_id=resource_id,
            raw_body=raw_body,
            headers=canonical_json(dict(headers)),
            verified=verified,
            recorded_at=self.clock.now(),
        )
        self.session.add(wh_event)
        self.session.flush()

        # Reconcile authorization if relevant
        auth_stmt = (
            select(PaymentAuthorization)
            .where(
                (PaymentAuthorization.authorization_id == resource_id)
                | (PaymentAuthorization.order_id == resource_id)
            )
            .limit(1)
        )
        auth = self.session.execute(auth_stmt).scalars().first()

        if auth:
            # Reconcile state based on webhook event_type without initiating captures.
            # Terminal states are immutable: a late void/expiry must never rewrite a captured authorization.
            if is_terminal(auth.state):
                pass
            elif event_type == "PAYMENT.AUTHORIZATION.VOIDED":
                auth.state = PaymentState.VOIDED.value
                auth.voided_at = self.clock.now()
                auth.void_reason = "Webhook void notification"
            elif event_type == "PAYMENT.AUTHORIZATION.EXPIRED":
                auth.state = PaymentState.EXPIRED.value

            append_event(
                session=self.session,
                purchase_id=auth.purchase_id,
                event_type="WEBHOOK_RECEIVED",
                actor="paypal_webhook",
                payload={
                    "event_id": event_id,
                    "event_type": event_type,
                    "resource_id": resource_id,
                },
                clock=self.clock,
            )

        self.session.commit()
        return {"status": "processed", "event_id": event_id, "event_type": event_type}

