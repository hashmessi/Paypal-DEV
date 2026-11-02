"""In-memory fake payment gateway implementation for tests and local demo mode."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

from app.core.canon import cents_to_dollar_str


class FakeGateway:
    """Implements PaymentGateway protocol with in-memory stores and zero external network calls."""

    def __init__(self) -> None:
        self.orders: dict[str, dict[str, Any]] = {}
        self.authorizations: dict[str, dict[str, Any]] = {}
        self.captures: dict[str, dict[str, Any]] = {}
        self.voids: dict[str, dict[str, Any]] = {}
        self.idempotency_records: dict[str, dict[str, Any]] = {}
        self.tracking_records: list[dict[str, Any]] = []
        self.fail_next_capture: bool = False
        self.fail_next_void: bool = False
        self.webhook_verify_result: bool = True

    async def create_order(
        self,
        amount_cents: int,
        currency: str,
        ref: str,
        custom_id: Optional[str] = None,
        return_url: str = "https://promiseloop.dev/checkout/return",
        cancel_url: str = "https://promiseloop.dev/checkout/cancel",
    ) -> dict[str, Any]:
        order_id = f"ORDER-{uuid.uuid4().hex[:12].upper()}"
        order_data = {
            "order_id": order_id,
            "status": "CREATED",
            "intent": "AUTHORIZE",
            "amount_cents": amount_cents,
            "currency": currency,
            "ref": ref,
            "custom_id": custom_id,
            "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.orders[order_id] = order_data
        return order_data

    async def authorize_order(
        self,
        order_id: str,
    ) -> dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            # Generate deterministic fallback if order was not pre-created
            amount_cents = 8999
            currency = "USD"
        else:
            amount_cents = order["amount_cents"]
            currency = order["currency"]
            order["status"] = "COMPLETED"

        auth_id = f"AUTH-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)
        exp = now + timedelta(days=29)

        auth_data = {
            "authorization_id": auth_id,
            "order_id": order_id,
            "status": "CREATED",
            "amount_cents": amount_cents,
            "currency": currency,
            "expiration_time": exp.isoformat(),
            "created_at": now.isoformat(),
            "raw_response": {
                "id": auth_id,
                "status": "CREATED",
                "amount": {
                    "currency_code": currency,
                    "value": cents_to_dollar_str(amount_cents),
                },
                "expiration_time": exp.isoformat(),
            },
        }
        self.authorizations[auth_id] = auth_data
        return auth_data

    async def capture_authorization(
        self,
        authorization_id: str,
        amount_cents: int,
        currency: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        if self.fail_next_capture:
            self.fail_next_capture = False
            raise RuntimeError("Simulated gateway network failure during capture")

        # Gateway-level idempotency
        if request_id in self.idempotency_records:
            return self.idempotency_records[request_id]

        auth = self.authorizations.get(authorization_id)
        if auth and auth.get("status") in ("CAPTURED", "VOIDED"):
            raise ValueError(f"Authorization {authorization_id} is already {auth.get('status')}")

        capture_id = f"CAP-{uuid.uuid4().hex[:12].upper()}"
        capture_data = {
            "capture_id": capture_id,
            "authorization_id": authorization_id,
            "status": "COMPLETED",
            "amount_cents": amount_cents,
            "currency": currency,
            "request_id": request_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "raw_response": {
                "id": capture_id,
                "status": "COMPLETED",
                "amount": {
                    "currency_code": currency,
                    "value": cents_to_dollar_str(amount_cents),
                },
            },
        }
        self.captures[capture_id] = capture_data
        if auth:
            auth["status"] = "CAPTURED"
            auth["capture_id"] = capture_id

        self.idempotency_records[request_id] = capture_data
        return capture_data

    async def void_authorization(
        self,
        authorization_id: str,
        request_id: str,
        note_to_payer: str = "",
    ) -> dict[str, Any]:
        if self.fail_next_void:
            self.fail_next_void = False
            raise RuntimeError("Simulated gateway network failure during void")

        if request_id in self.idempotency_records:
            return self.idempotency_records[request_id]

        auth = self.authorizations.get(authorization_id)
        if auth and auth.get("status") in ("CAPTURED", "VOIDED"):
            raise ValueError(f"Authorization {authorization_id} is already {auth.get('status')}")

        void_data = {
            "authorization_id": authorization_id,
            "status": "VOIDED",
            "request_id": request_id,
            "voided_at": datetime.now(timezone.utc).isoformat(),
            "raw_response": {
                "id": authorization_id,
                "status": "VOIDED",
            },
        }
        self.voids[authorization_id] = void_data
        if auth:
            auth["status"] = "VOIDED"

        self.idempotency_records[request_id] = void_data
        return void_data

    async def reconcile_authorization(
        self,
        authorization_id: str,
    ) -> dict[str, Any]:
        auth = self.authorizations.get(authorization_id)
        if auth:
            return {
                "authorization_id": authorization_id,
                "status": auth["status"],
                "expiration_time": auth.get("expiration_time"),
                "amount_cents": auth["amount_cents"],
                "currency": auth["currency"],
                "raw_response": auth.get("raw_response", {}),
            }
        return {
            "authorization_id": authorization_id,
            "status": "CREATED",
            "expiration_time": (datetime.now(timezone.utc) + timedelta(days=29)).isoformat(),
            "amount_cents": 8999,
            "currency": "USD",
            "raw_response": {},
        }

    async def verify_webhook_signature(
        self,
        headers: dict[str, str],
        raw_body: str,
        webhook_id: str,
    ) -> bool:
        return self.webhook_verify_result

    async def push_tracking(
        self,
        order_id: str,
        capture_id: str,
        carrier: str,
        tracking_number: str,
        sku: str,
    ) -> dict[str, Any]:
        record = {
            "order_id": order_id,
            "capture_id": capture_id,
            "carrier": carrier,
            "tracking_number": tracking_number,
            "sku": sku,
            "status": "TRACKING_RECORDED",
        }
        self.tracking_records.append(record)
        return record

