"""PayPal Webhook Signature Verification logic."""

import logging
from typing import Any, Mapping

from app.core.config import settings
from app.payments.port import PaymentGateway

logger = logging.getLogger(__name__)


async def verify_webhook_signature(
    headers: Mapping[str, str],
    raw_body: str,
    gateway: PaymentGateway,
    webhook_id: str = "",
) -> bool:
    """Verify PayPal webhook notification signature against gateway using the exact raw body bytes."""
    wh_id = webhook_id or settings.PAYPAL_WEBHOOK_ID

    # Normalize header keys to uppercase for robust lookup
    norm_headers = {k.upper(): v for k, v in headers.items()}

    required_headers = [
        "PAYPAL-AUTH-ALGO",
        "PAYPAL-CERT-URL",
        "PAYPAL-TRANSMISSION-ID",
        "PAYPAL-TRANSMISSION-SIG",
        "PAYPAL-TRANSMISSION-TIME",
    ]

    missing = [h for h in required_headers if h not in norm_headers]
    if missing:
        logger.warning("Webhook request missing required PayPal security headers: %s", missing)
        return False

    return await gateway.verify_webhook_signature(
        headers=dict(norm_headers),
        raw_body=raw_body,
        webhook_id=wh_id,
    )

