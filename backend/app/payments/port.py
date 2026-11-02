"""Payment gateway interface (Port) in hexagonal / clean architecture.

Both PayPalGateway (production / sandbox) and FakeGateway (tests) implement this protocol.
"""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class PaymentGateway(Protocol):
    """Abstract interface for payment operations."""

    async def create_order(
        self,
        amount_cents: int,
        currency: str,
        ref: str,
        custom_id: Optional[str] = None,
        return_url: str = "https://promiseloop.dev/checkout/return",
        cancel_url: str = "https://promiseloop.dev/checkout/cancel",
    ) -> dict[str, Any]:
        """Create a PayPal Order with intent='AUTHORIZE'.

        Returns:
            dict containing at minimum: 'order_id', 'status', 'approval_url'
        """
        ...

    async def authorize_order(
        self,
        order_id: str,
    ) -> dict[str, Any]:
        """Authorize an approved PayPal Order (places hold on buyer funds).

        Returns:
            dict containing at minimum:
            'authorization_id', 'status', 'amount_cents', 'currency', 'expiration_time'
        """
        ...

    async def capture_authorization(
        self,
        authorization_id: str,
        amount_cents: int,
        currency: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        """Capture an authorization.

        Must pass request_id as PayPal-Request-Id header.
        Returns:
            dict containing at minimum:
            'capture_id', 'status', 'amount_cents', 'currency'
        """
        ...

    async def void_authorization(
        self,
        authorization_id: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        """Void an authorization (releases buyer hold).

        Must pass request_id as PayPal-Request-Id header.
        Returns:
            dict containing at minimum: 'authorization_id', 'status'
        """
        ...

    async def reconcile_authorization(
        self,
        authorization_id: str,
    ) -> dict[str, Any]:
        """Fetch current state of authorization from gateway.

        Returns:
            dict containing at minimum: 'authorization_id', 'status', 'expiration_time'
        """
        ...

    async def verify_webhook_signature(
        self,
        headers: dict[str, str],
        raw_body: str,
        webhook_id: str,
    ) -> bool:
        """Verify authenticity of PayPal webhook notification."""
        ...

    async def push_tracking(
        self,
        order_id: str,
        capture_id: str,
        carrier: str,
        tracking_number: str,
        sku: str,
    ) -> dict[str, Any]:
        """Push verified shipment tracking and item SKU to PayPal Orders v2 tracking API."""
        ...

