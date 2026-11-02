# Phase 05: Product Optimization to 50/50 & Winning Readiness — Plan

**Phase:** 05-product-optimization-50-50  
**Goal:** Execute slices S0 through S11 to transition PromiseLoop from baseline 30/50 to the Top #1 50/50 score against the PayPal Devpost Judging Criteria, securing Tie-Breaker dominance.  
**Reference Document:** `.planning/OPTIMIZATION-PLAN.md`

---

## Work Breakdown Structure

### Plan 1: S0 — Checkpoint & Working Tree Harmonization
- **Objective:** Secure uncommitted changes (AP2 mandate export, Orders v2 tracking push, Verify page WebCrypto recomputation).
- **Files:**
  - `backend/app/receipt/ap2.py`
  - `backend/tests/test_ap2.py`
  - `backend/tests/test_tracking_push.py`
  - `frontend/src/pages/Receipt.tsx`
  - `frontend/src/pages/Verify.tsx`
- **Verification:** `python -m pytest -q tests/test_ap2.py tests/test_tracking_push.py` (all pass).

### Plan 2: S1 — Decouple Gateway Simulation from Demo Mode (Stage One Fix)
- **Objective:** Allow genuine PayPal Sandbox calls when `PAYPAL_CLIENT_ID` is present, while retaining `DEMO_MODE` solely for scenario tooling.
- **Files:**
  - `backend/app/proof/counterfactual.py`
  - `backend/app/api/deps.py`
  - `backend/tests/test_gateway_contract.py`
- **Verification:** Unit tests confirming `get_gateway()` selects `PayPalGateway` when configured with credentials, independent of `DEMO_MODE`.

### Plan 3: S2 & S4 — Real PayPal Sandbox Lane & Truth Panel
- **Objective:** Complete real Sandbox create → authorize → drift-check → capture/void flow; surface live PayPal IDs on screen.
- **Files:**
  - `frontend/src/components/domain/PayPalAuthorizeButton.tsx`
  - `frontend/src/pages/Receipt.tsx`
  - `frontend/src/components/domain/StatusPill.tsx`
- **Verification:** Real PayPal order ID, authorization ID, and capture ID recorded; live vs simulated badging active on all money surfaces.

### Plan 4: S3 — Public Deploy, Keep-Warm & Webhook Postback Verification
- **Objective:** Public HTTPS URL on Render with live PayPal webhook registration and cryptographic signature validation.
- **Files:**
  - `render.yaml`
  - External keep-warm ping configuration.
- **Verification:** `curl -s https://<render-url>/health` returns 200; real PayPal webhook postback verified.

### Plan 5: S5 — Two-Lane Golden Path UI & 6-Stage Progress HUD
- **Objective:** Redesign `/` landing page with clear Two-Lane choice architecture (Live Sandbox vs 30-sec Instant Demo) and embed 6-stage Promise Progression HUD.
- **Files:**
  - `frontend/src/pages/Start.tsx`
  - `frontend/src/components/ui/Navbar.tsx`
  - `frontend/src/components/domain/Stepper.tsx`
- **Verification:** Clean visual flow on desktop and mobile 375px; zero dead ends.

### Plan 6: S6 & S7 — Real Catalog Data, AI Transparency & Prompt Injection Defense
- **Objective:** Ingest real Channel3 catalog snapshots, display Gemini extraction metadata, and test adversarial prompt injection in shipping metadata.
- **Files:**
  - `backend/app/discovery/channel3.py`
  - `backend/app/intent/service.py`
  - `frontend/src/components/domain/ScenarioConsole.tsx`
  - `backend/tests/test_acceptance_cases.py`
- **Verification:** Invariant gate blocks capture on injected shipping text (`python -m pytest -q tests/test_acceptance_cases.py`).

### Plan 7: S8 & S9 — Primary-Sourced Economics & Defensive State Sweep
- **Objective:** Embed LexisNexis $3.75 dispute cost citations into UI/docs; harden cold-start and popup cancellation states.
- **Files:**
  - `README.md`
  - `frontend/src/pages/Proof.tsx`
  - `frontend/src/components/ui/ColdStartNotice.tsx`
- **Verification:** 18 proof scenarios benchmarked; simulated popup cancellation recovers cleanly.

### Plan 8: S10 & S11 — Winning 2:25 Video Production & Zero-Placeholder Devpost Submission
- **Objective:** Record high-tempo video following the 6-act screenplay; clean all placeholders from README.md and submit on Devpost.
- **Files:**
  - `README.md`
  - Devpost Submission text & video link.
- **Verification:** `grep -En "<.*fill in|<LIVE_URL" README.md` returns 0; `bash scripts/verify.sh` returns 7/7 PASS.

