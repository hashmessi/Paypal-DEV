"""PayPal Webhooks ingestion endpoint using raw body signature verification."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_clock, get_gateway
from app.core.clock import Clock
from app.core.config import settings
from app.core.db import get_db
from app.payments.port import PaymentGateway
from app.webhooks.processor import WebhookProcessor
from app.webhooks.verify import verify_webhook_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/paypal")
async def handle_paypal_webhook(
    request: Request,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_gateway),
    clock: Clock = Depends(get_clock),
):
    """Receive and verify PayPal webhook notification.

    PAY-06:
    - Signature verification performed against exact raw request body bytes.
    - Idempotent deduplication: identical event_ids return HTTP 200 without duplicate action.
    - Does NOT trigger automated capture under any circumstance.
    """
    body_bytes = await request.body()
    raw_body = body_bytes.decode("utf-8")

    # In sandbox/live, verify cryptographic signature
    # In test/demo mode with FakeGateway, verify_webhook_signature returns gateway mock value
    is_valid = await verify_webhook_signature(
        headers=request.headers,
        raw_body=raw_body,
        gateway=gateway,
        webhook_id=settings.PAYPAL_WEBHOOK_ID,
    )

    if not is_valid:
        logger.warning("Rejected unverified PayPal webhook signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PayPal webhook signature",
        )

    processor = WebhookProcessor(session=db, clock=clock)
    try:
        result = await processor.process_event(
            headers=request.headers,
            raw_body=raw_body,
            verified=True,
        )
        return result
    except Exception as err:
        logger.error("Error processing webhook: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing error: {str(err)}",
        )

