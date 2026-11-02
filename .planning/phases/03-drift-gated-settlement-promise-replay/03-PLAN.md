# Phase 03: Drift-Gated Settlement + Promise Replay — Plan

**Phase:** 03-drift-gated-settlement-promise-replay  
**Goal:** Deliver deterministic invariant gate evaluation, fulfillment evidence ingestion, scenario console triggers, seller correction lifecycle, settlement gating, plain-language finding explanations, and 10-step Promise Replay audit.  

---

## Work Breakdown Structure

### Plan 1: Database Models & Schema Updates
- Update `backend/app/core/models.py`:
  - `FulfillmentEvidence`: typed evidence records with source, external_event_id, trust level, synthetic flag, unique constraint.
  - `GateEvaluationRecord`: stores gate evaluation history, outcomes, status pills, and findings.
- Update `backend/schema.sql` with new tables and indexes.

### Plan 2: Pure Deterministic Drift Engine & Explainer
- `backend/app/drift/models.py`: `GateOutcome` (MATCH, DRIFT, HOLD, PROHIBITED), `Finding`, `GateEvaluation`.
- `backend/app/drift/invariants.py`: Implementation of invariant checks (condition, SKU/color, carrier acceptance, ETA/deadline, authorization expiry).
- `backend/app/drift/engine.py`: Pure deterministic `evaluate(receipt, auth, evidence_list, now: datetime)`.
- `backend/app/drift/explainer.py`: Template and LLM-assisted plain-language explanation generator (DRIFT-04, SEC-02).

### Plan 3: Fulfillment Evidence Ingestion & Scenario Console
- `backend/app/fulfillment/models.py`: Ingestion request/response schemas.
- `backend/app/fulfillment/service.py`: Deduplicated evidence ingestion, auto gate re-evaluation, ledger event logging (`EVIDENCE_INGESTED`, `GATE_EVALUATED`).
- `backend/app/fulfillment/scenarios.py`: Synthetic Scenario Console engine supporting all 8 triggers:
  1. `refurbished` (DRIFT -> CAPTURE BLOCKED)
  2. `wrong_color` (DRIFT -> CAPTURE BLOCKED)
  3. `corrected` (matching SKU + carrier ACCEPTED -> MATCH)
  4. `label_only` (LABEL_CREATED -> HOLD)
  5. `late_eta` (ETA past deadline -> HOLD)
  6. `duplicate_event` (deduplication check)
  7. `price_change` (merchant quote shift -> STALE)
  8. `advance_clock` (past expiration_time -> PROHIBITED / RENEWAL_REQUIRED)

### Plan 4: Drift-Gated Settlement & 10-Step Promise Replay
- Update `backend/app/payments/service.py` to enforce PAY-02:
  - Only capture when `gate.outcome == "MATCH"`.
  - Raise `CaptureBlockedByGateError` if gate is DRIFT, HOLD, or PROHIBITED.
- `backend/app/replay/service.py`: Assembles the full 10-step Promise Replay timeline with highlighted divergence step on drift (UI-03).

### Plan 5: REST API Routers
- `backend/app/api/fulfillment.py`: `POST /fulfillment/evidence`, `POST /fulfillment/scenarios/{purchase_id}`
- `backend/app/api/gate.py`: `GET /purchases/{purchase_id}/gate`, `POST /purchases/{purchase_id}/settle`
- Mount routers in `backend/app/main.py`.

### Plan 6: Automated Test Suite & Verification Gate
- `backend/tests/test_drift_engine.py`: Invariant rules testing (INV-01 through INV-06).
- `backend/tests/test_fulfillment_ingestion.py`: Evidence ingestion, deduplication, trust levels.
- `backend/tests/test_gated_settlement.py`: Settlement gating (PAY-02, PAY-07).
- `backend/tests/test_acceptance_cases.py`: All 11 acceptance cases (PROOF-01, SEC-02).
- Verification with `pytest` and `scripts/verify.sh`.

