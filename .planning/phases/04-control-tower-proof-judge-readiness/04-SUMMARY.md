# Phase 04: Control Tower, Proof & Judge Readiness — Plan & Verification Record

**Date:** 2026-11-02
**Status:** PARTIALLY VALIDATED — code items done; human/deploy items open (see Open)
**Gate:** `bash scripts/verify.sh` → 7/7 PASS; backend 85 passed

## Plan (executed)
1. Proof runner: 18 labeled scenarios through the real `drift.engine.evaluate`; 6 metrics with numerator/denominator computed, not hardcoded (PROOF-02).
2. Console API: `GET /tower`, `/events`, `/proof`, `/promises/{id}`, `POST /demo/run` (fresh clock-relative approved receipt + authorization per call, DEPLOY-03) (UI-04).
3. Guards: `X-Admin-Token` on `/demo/scenarios` (fails closed when `ADMIN_TOKEN` unset); per-IP rate limit on `/intent/extract` (SEC-03).
4. SEC-01: test walks the import graph from LLM-facing modules and fails on any path to payments/webhooks/fulfillment/api/receipt.service; test asserts capture/void exist only under `/purchases/` and never call the gateway directly.
5. Frontend `lib/api.ts` aligned to real shapes (replay adapter, scenarios, void, receipt, verify, `/demo/run`).
6. README, LICENSE (MIT), render.yaml (`PYTHON_VERSION`, generated `ADMIN_TOKEN`, DB-expiry note).

## Bug found by the proof suite (fixed)
Scenario S09: refurbished item followed by a carrier event that omits item fields returned **MATCH** (gate read only the latest event), so capture would have been allowed. Fixed in `backend/app/drift/invariants.py` (each of condition/SKU/color is read from the latest event that carries it). Regression: `test_refurbished_then_silent_followup_still_drifts`.

## Validated
- `python -m pytest -q` → 85 passed (incl. `tests/test_phase4.py`, 8 new)
- `bash scripts/verify.sh` → RESULT: PASS (7 passed)

## Open (not done / not verifiable here)
- **PROOF-04** demo video (<3:00, by Nov 10) and Devpost submission: human tasks.
- **DEPLOY-02** live Render deploy, public URL, Postgres renewal past Dec 21: not deployed from here. README has `<LIVE_URL>` and `<SANDBOX_BUYER…>` placeholders to fill.
- **PROOF-03** APIMatic log is a placeholder (plugin not run); AP2 v0.2 mapping is conceptual and unchecked against the spec.
- UI-04 reconcile/void actions work through the new API in tests only for the read path; the Tower page was not exercised in a browser. Operator void/reconcile endpoints are not token-protected (void/capture remain gate/state-machine protected); decide whether judges need them open.
- Proof metrics use a fixed clock and in-memory objects; "duplicate actions" runs against the fake gateway, not PayPal Sandbox.
- `import-linter` not added; the same contract is an AST test in pytest (runs inside the gate).
