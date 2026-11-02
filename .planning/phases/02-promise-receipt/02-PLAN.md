# Phase 02: Promise Receipt — Plan

**Phase:** 02-promise-receipt  
**Goal:** Deliver natural language intent extraction, Channel3 product discovery, RFC 8785 canonical Promise Receipt compilation, budget gating, versioned approval, and PayPal `custom_id` binding.  

---

## Work Breakdown Structure

### Plan 1: Database Models & Schema Updates
- Update `backend/app/core/models.py`:
  - `PromiseReceipt`: versioned, stores canonical_payload, receipt_hash, constraints, snapshot, quote, status (draft, approved, stale).
  - `ExtractionCache`: caches instruction hash -> extracted constraints.
- Update `backend/schema.sql` with table definitions and immutability triggers.

### Plan 2: Intent Extractor & Multi-Tier Fallback
- `backend/app/intent/models.py`: Typed schemas for constraints, validation, minor cent conversions.
- `backend/app/intent/fallback.py`: Deterministic rule-based extractor using regular expressions.
- `backend/app/intent/extractor.py`: Multi-tier orchestration:
  1. Google Gemini API with structured JSON output.
  2. OpenRouter free model fallback.
  3. Deterministic rule-based fallback.
  - Extraction caching by SHA-256 digest of normalized instruction.
  - Relative deadline calculation in code against `Clock` (never LLM-generated calendar dates).

### Plan 3: Product Discovery & Merchant Quote Adapter
- `backend/app/discovery/models.py`: Candidate, offer, snapshot, and merchant quote models.
- `backend/app/discovery/catalog.py`: Realistic synthetic headphone candidate dataset (Sony WH-1000XM5 in Black/Silver, Certified Refurbished, and Unverified).
- `backend/app/discovery/adapter.py`: Discovery adapter implementing Channel3 search:
  - Preserves exact raw response bytes.
  - Strictly maps `condition: null` -> `UNVERIFIED`.
  - Rejects non-USD offers.
  - Formats merchant quote with `"Sandbox stand-in for <domain>"`.

### Plan 4: Canonical Receipt Compiler & Approval Service
- `backend/app/receipt/models.py`: Receipt payload schemas.
- `backend/app/receipt/compiler.py`:
  - Canonical JSON RFC 8785 formatting.
  - Rejection of floating point amounts.
  - SHA-256 digest computation (`receipt_hash`).
  - Budget gate: rejects with `BudgetExceededError` if quote > buyer's max.
- `backend/app/receipt/service.py`:
  - Receipt lifecycle: compile -> approve -> mark stale on merchant change.
  - Strict approval gate: rejects approval with 409 Conflict if hash does not match current version.
  - DB immutability check.
  - Decision ledger event logging (`RECEIPT_COMPILED`, `RECEIPT_APPROVED`, `RECEIPT_STALE`).

### Plan 5: REST API Routers & PayPal custom_id Binding
- `backend/app/api/intent.py`: `POST /intent/extract`
- `backend/app/api/discovery.py`: `GET /discovery/search`, `POST /discovery/quote`
- `backend/app/api/receipts.py`: `POST /receipts/compile`, `POST /receipts/{id}/approve`, `GET /receipts/{id}`
- Update `backend/app/api/checkout.py` and `backend/app/payments/service.py`:
  - Pass `receipt_hash` into PayPal Order creation `custom_id` (PAY-08).

### Plan 6: Automated Test Suite & Verification Gate
- `backend/tests/test_intent_extraction.py` (INTENT-01, INTENT-02, INTENT-03)
- `backend/tests/test_discovery.py` (DISC-01, DISC-02, DISC-03)
- `backend/tests/test_receipt_compiler.py` (RCPT-01, RCPT-02, golden vector)
- `backend/tests/test_receipt_approval.py` (RCPT-03, RCPT-04, 409 conflict, immutability)
- `backend/tests/test_paypal_receipt_binding.py` (PAY-08)
- Verify with `pytest` and `scripts/verify.sh`.

