"""PayPal REST API integration implementing PaymentGateway port.

Uses httpx for asynchronous HTTP communication with PayPal sandbox / live endpoints.
Maintains cached OAuth2 access token and issues deterministic PayPal-Request-Id headers.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Optional

try:
    import httpx
except ImportError:
    import httpx2 as httpx

from app.core.canon import cents_to_dollar_str, dollar_str_to_cents
from app.core.config import settings

logger = logging.getLogger(__name__)


class PayPalApiError(Exception):
    """Exception raised when PayPal REST API returns an error response."""

    def __init__(self, status_code: int, error_name: str, message: str, details: Any = None) -> None:
        self.status_code = status_code
        self.error_name = error_name
        self.message = message
        self.details = details
        super().__init__(f"PayPal API Error [{status_code}] {error_name}: {message}")


class PayPalGateway:
    """Production and Sandbox PayPal REST API adapter."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> None:
        self.client_id = client_id or settings.PAYPAL_CLIENT_ID
        self.client_secret = client_secret or settings.PAYPAL_CLIENT_SECRET
        self.api_base = (api_base or settings.PAYPAL_API_BASE).rstrip("/")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """Fetch or return cached OAuth2 bearer token."""
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token

        url = f"{self.api_base}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers=headers,
                data=data,
                auth=(self.client_id, self.client_secret),
                timeout=20.0,
            )

        if resp.status_code != 200:
            logger.error("Failed to authenticate with PayPal: %s %s", resp.status_code, resp.text)
            raise PayPalApiError(
                status_code=resp.status_code,
                error_name="AUTHENTICATION_FAILURE",
                message=f"PayPal auth failed: {resp.text}",
            )

        payload = resp.json()
        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        # Refresh 60 seconds before expiration
        self._token_expires_at = datetime.fromtimestamp(
            now.timestamp() + max(expires_in - 60, 60), tz=timezone.utc
        )
        return self._access_token

    async def _auth_headers(self, request_id: Optional[str] = None) -> dict[str, str]:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        return headers

    async def create_order(
        self,
        amount_cents: int,
        currency: str,
        ref: str,
        custom_id: Optional[str] = None,
        return_url: str = "https://promiseloop.dev/checkout/return",
        cancel_url: str = "https://promiseloop.dev/checkout/cancel",
    ) -> dict[str, Any]:
        """Create a PayPal Order with intent='AUTHORIZE' and optional receipt hash custom_id."""
        url = f"{self.api_base}/v2/checkout/orders"
        headers = await self._auth_headers()
        purchase_unit: dict[str, Any] = {
            "reference_id": ref,
            "amount": {
                "currency_code": currency,
                "value": cents_to_dollar_str(amount_cents),
            },
            "description": f"PromiseLoop Purchase {ref}",
        }
        if custom_id:
            purchase_unit["custom_id"] = custom_id

        payload = {
            "intent": "AUTHORIZE",
            "purchase_units": [purchase_unit],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                        "brand_name": "PromiseLoop Agentic Commerce",
                        "locale": "en-US",
                        "landing_page": "LOGIN",
                        "user_action": "CONTINUE",
                        "return_url": return_url,
                        "cancel_url": cancel_url,
                    }
                }
            },
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)

        data = resp.json()
        if resp.status_code not in (200, 201):
            raise PayPalApiError(
                resp.status_code,
                data.get("name", "ORDER_CREATION_FAILED"),
                data.get("message", "Unable to create PayPal order"),
                data.get("details"),
            )

        order_id = data["id"]
        approval_url = ""
        for link in data.get("links", []):
            if link.get("rel") in ("payer-action", "approve"):
                approval_url = link.get("href", "")
                break

        return {
            "order_id": order_id,
            "status": data.get("status", "CREATED"),
            "approval_url": approval_url,
            "raw_response": data,
        }

    async def authorize_order(
        self,
        order_id: str,
    ) -> dict[str, Any]:
        """Authorize an approved PayPal Order."""
        url = f"{self.api_base}/v2/checkout/orders/{order_id}/authorize"
        headers = await self._auth_headers()

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json={}, timeout=20.0)

        data = resp.json()
        if resp.status_code not in (200, 201):
            raise PayPalApiError(
                resp.status_code,
                data.get("name", "ORDER_AUTHORIZATION_FAILED"),
                data.get("message", "Unable to authorize PayPal order"),
                data.get("details"),
            )

        try:
            purchase_unit = data["purchase_units"][0]
            auth_info = purchase_unit["payments"]["authorizations"][0]
            auth_id = auth_info["id"]
            status = auth_info.get("status", "CREATED")
            amount_val = auth_info["amount"]["value"]
            currency = auth_info["amount"]["currency_code"]
            expiration_time = auth_info.get("expiration_time")
        except (KeyError, IndexError) as err:
            raise PayPalApiError(
                resp.status_code,
                "MALFORMED_AUTHORIZATION_RESPONSE",
                f"Missing authorization payload fields: {err}",
                data,
            )

        return {
            "authorization_id": auth_id,
            "order_id": order_id,
            "status": status,
            "amount_cents": dollar_str_to_cents(amount_val),
            "currency": currency,
            "expiration_time": expiration_time,
            "raw_response": data,
        }

    async def capture_authorization(
        self,
        authorization_id: str,
        amount_cents: int,
        currency: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        """Capture an authorized hold on PayPal."""
        url = f"{self.api_base}/v2/payments/authorizations/{authorization_id}/capture"
        headers = await self._auth_headers(request_id=request_id)
        payload: dict[str, Any] = {
            "amount": {
                "currency_code": currency,
                "value": cents_to_dollar_str(amount_cents),
            },
            "final_capture": True,
        }
        if note_to_payer:
            payload["note_to_payer"] = note_to_payer

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)

        data = resp.json()
        if resp.status_code not in (200, 201):
            raise PayPalApiError(
                resp.status_code,
                data.get("name", "CAPTURE_FAILED"),
                data.get("message", "Unable to capture authorization"),
                data.get("details"),
            )

        return {
            "capture_id": data["id"],
            "authorization_id": authorization_id,
            "status": data.get("status", "COMPLETED"),
            "amount_cents": dollar_str_to_cents(data["amount"]["value"]),
            "currency": data["amount"]["currency_code"],
            "raw_response": data,
        }

    async def void_authorization(
        self,
        authorization_id: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        """Void an authorization on PayPal."""
        url = f"{self.api_base}/v2/payments/authorizations/{authorization_id}/void"
        headers = await self._auth_headers(request_id=request_id)
        payload = {}
        if note_to_payer:
            payload["note_to_payer"] = note_to_payer

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=20.0)

        if resp.status_code in (200, 204):
            return {
                "authorization_id": authorization_id,
                "status": "VOIDED",
                "raw_response": resp.json() if resp.text else {},
            }

        data = resp.json() if resp.text else {}
        raise PayPalApiError(
            resp.status_code,
            data.get("name", "VOID_FAILED"),
            data.get("message", "Unable to void authorization"),
            data.get("details"),
        )

    async def reconcile_authorization(
        self,
        authorization_id: str,
    ) -> dict[str, Any]:
        """Fetch status of authorization from PayPal."""
        url = f"{self.api_base}/v2/payments/authorizations/{authorization_id}"
        headers = await self._auth_headers()

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=20.0)

        data = resp.json()
        if resp.status_code != 200:
            raise PayPalApiError(
                resp.status_code,
                data.get("name", "RECONCILE_FAILED"),
                data.get("message", f"Unable to fetch authorization {authorization_id}"),
                data.get("details"),
            )

        return {
            "authorization_id": data["id"],
            "status": data.get("status", "CREATED"),
            "expiration_time": data.get("expiration_time"),
            "amount_cents": dollar_str_to_cents(data["amount"]["value"]),
            "currency": data["amount"]["currency_code"],
            "raw_response": data,
        }

    async def verify_webhook_signature(
        self,
        headers: dict[str, str],
        raw_body: str,
        webhook_id: str,
    ) -> bool:
        """Verify webhook signature via PayPal REST API endpoint."""
        url = f"{self.api_base}/v1/notifications/verify-webhook-signature"
        auth_headers = await self._auth_headers()

        # Extract PayPal webhook headers (case-insensitive)
        hdr_map = {k.upper(): v for k, v in headers.items()}
        auth_algo = hdr_map.get("PAYPAL-AUTH-ALGO", "")
        cert_url = hdr_map.get("PAYPAL-CERT-URL", "")
        transmission_id = hdr_map.get("PAYPAL-TRANSMISSION-ID", "")
        transmission_sig = hdr_map.get("PAYPAL-TRANSMISSION-SIG", "")
        transmission_time = hdr_map.get("PAYPAL-TRANSMISSION-TIME", "")

        if not all([auth_algo, cert_url, transmission_id, transmission_sig, transmission_time]):
            logger.warning("Missing required PayPal webhook headers for signature verification")
            return False

        try:
            event_body = json.loads(raw_body)
        except Exception:
            logger.warning("Webhook raw_body is not valid JSON")
            return False

        verify_payload = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": webhook_id,
            "webhook_event": event_body,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=auth_headers, json=verify_payload, timeout=20.0)

        if resp.status_code != 200:
            logger.error("PayPal webhook verification HTTP error: %s %s", resp.status_code, resp.text)
            return False

        result = resp.json()
        return result.get("verification_status") == "SUCCESS"

    async def push_tracking(
        self,
        order_id: str,
        capture_id: str,
        carrier: str,
        tracking_number: str,
        sku: str,
    ) -> dict[str, Any]:
        """Push verified shipment tracking and item SKU to PayPal Orders v2 tracking API."""
        url = f"{self.api_base}/v2/checkout/orders/{order_id}/track"
        auth_headers = await self._auth_headers()
        payload = {
            "capture_id": capture_id,
            "tracking_number": tracking_number,
            "carrier": (carrier or "OTHER").upper(),
            "status": "SHIPPED",
            "items": [
                {
                    "name": "Verified Invariant Product",
                    "quantity": "1",
                    "sku": sku or "WH1000XM5-BLK-NEW",
                }
            ],
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=auth_headers, json=payload, timeout=20.0)
            if resp.status_code in (200, 201):
                logger.info("Successfully pushed tracking for order %s to PayPal", order_id)
                return resp.json()
            logger.warning("PayPal tracking push returned %s: %s", resp.status_code, resp.text)
            return {"status": "FAILED", "code": resp.status_code, "detail": resp.text}
        except Exception as e:
            logger.error("Failed to push tracking to PayPal for order %s: %s", order_id, e)
            return {"status": "ERROR", "error": str(e)}
