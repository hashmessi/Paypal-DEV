# Phase 01: Money Spine on a Public URL — Plan

**Phase:** 01-money-spine-on-a-public-url
**Goal:** Deliver the complete financial backbone, state machine, PayPal adapter, hash-chained ledger, and webhook processor, tested and ready for public Render deployment.

---

## Work Breakdown Structure

### Plan 1: Core Foundation & Database Models
- `backend/app/core/canon.py`: RFC 8785 canonical JSON serializer, SHA-256 calculator, integer minor units.
- `backend/app/core/clock.py`: Injectable clock protocols (`SystemClock`, `FixedClock`, `DemoOffsetClock`).
- `backend/app/core/config.py`: Pydantic settings for PayPal credentials, DB URL, Webhook ID, app environment.
- `backend/app/core/db.py`: SQLAlchemy session engine and transactional context managers.
- `backend/app/core/models.py`: Declarative ORM models:
  - `Purchase`
  - `PaymentAuthorization`
  - `FinancialAction` (idempotency key lock table)
  - `DecisionEvent` (hash-chained ledger)
  - `WebhookEvent` (deduplicated webhook log)
- `backend/schema.sql`: Full SQL schema with triggers.

### Plan 2: Payment State Machine & Gateways
- `backend/app/payments/state.py`: Payment state machine with transition validator.
- `backend/app/payments/port.py`: Abstract `PaymentGateway` protocol.
- `backend/app/payments/paypal.py`: Real PayPal REST Orders/Payments v2 client with OAuth2 token manager.
- `backend/app/payments/fake.py`: Full in-memory `FakeGateway` for zero-network testing.
- `backend/app/payments/service.py`: High-level payments service with idempotency checks and CAS updates.

### Plan 3: Hash-Chained Ledger & Webhook Verification
- `backend/app/ledger/events.py`: `append_event` appending to ledger with cryptographic hash chaining.
- `backend/app/ledger/verify.py`: `verify_chain` verifying continuous SHA-256 hashes.
- `backend/app/webhooks/verify.py`: PayPal signature verification (postback & test cert).
- `backend/app/webhooks/processor.py`: Deduplicated webhook ingestion and ledger recording.

### Plan 4: FastAPI REST Routers & Deployment Spec
- `backend/app/api/checkout.py`: `/checkout/orders` and `/checkout/orders/{id}/authorize`
- `backend/app/api/payments.py`: `/purchases/{id}/capture`, `/purchases/{id}/void`, `/purchases/{id}/reconcile`
- `backend/app/api/ledger.py`: `/purchases/{id}/replay`, `/purchases/{id}/verify`
- `backend/app/api/webhooks.py`: `/webhooks/paypal` raw body handler
- `backend/app/main.py`: App factory with dependency injection and CORS.
- `render.yaml`: Blueprint configuration for Render deployment (DEPLOY-01).

### Plan 5: Automated Test Suite & Verification
- `backend/tests/conftest.py`: Test fixtures with in-memory SQLite and `FakeGateway`.
- `backend/tests/test_state_machine.py`: Legal/illegal transitions (PAY-04).
- `backend/tests/test_idempotency.py`: Duplicate capture/void handling and CAS locks (PAY-05).
- `backend/tests/test_gateway_contract.py`: Gateway protocol contract tests.
- `backend/tests/test_ledger_chain.py`: Tamper-evident ledger hashing & verification (LEDG-01).
- `backend/tests/test_webhooks.py`: Raw signature validation and deduplication (PAY-06).
- `backend/tests/test_api_endpoints.py`: End-to-end FastAPI integration testing.
- Verification with `pytest` and `scripts/verify.sh`.

