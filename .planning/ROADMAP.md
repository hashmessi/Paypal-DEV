# Roadmap: PromiseLoop

## Overview

PromiseLoop is built as four vertical slices that follow the money dependency chain. Phase 1 gets a real PayPal Sandbox authorization onto a public URL. Phase 2 adds the Promise Receipt that the authorization is bound to. Phase 3 adds the deterministic drift gate that decides whether money moves, plus Promise Replay. Phase 4 adds the judge-facing surfaces (control tower and proof) and the submission. Every phase ends in a live, demoable act. Deadline: Nov 12, 2026 12:00 PT. Hard gate: Phase 1 must pass by Nov 2 or scope gets cut right away, never padded out with more AI features.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Money Spine on a Public URL** - Real Sandbox authorize, capture and void with idempotency, webhooks and the ledger, deployed on Render (hard gate Nov 2)
- [ ] **Phase 2: Promise Receipt** - Instruction to constraints to Channel3 offer to hashed, buyer-approved receipt bound to a real authorization (Acts 1-4, ~Nov 3-4)
- [ ] **Phase 3: Drift-Gated Settlement + Promise Replay** - Fulfillment evidence drives a pure drift engine that blocks or permits capture; Replay shows the full lifecycle (Acts 5-8, ~Nov 5-8)
- [ ] **Phase 4: Control Tower, Proof & Judge Readiness** - AG Grid tower, metrics, security pass, durable deploy, README, video and Devpost submission (~Nov 9-12)

## Phase Details

### Phase 1: Money Spine on a Public URL
**Goal**: A real PayPal Sandbox authorization can be created, captured or voided exactly once from the deployed Render URL, with every financial event appended to a tamper-evident ledger
**Mode:** mvp
**Depends on**: Nothing (first phase)
**Requirements**: PAY-01, PAY-03, PAY-04, PAY-05, PAY-06, LEDG-01, DEPLOY-01
**Success Criteria** (what must be TRUE):
  1. From the public Render HTTPS URL, a Sandbox buyer approves an `AUTHORIZE` order in the PayPal popup and the server stores order ID, authorization ID and `expiration_time`; that authorization can then be captured
  2. A second authorized order can be voided with a reason code; a later capture attempt on it is refused locally without any PayPal call
  3. Sending the same capture twice returns the same capture ID and leaves exactly one capture in the Sandbox; illegal payment-state transitions are rejected
  4. A real PayPal webhook delivered to the public URL is postback-verified, stored once even if redelivered, and a tampered body is rejected
  5. Every order, authorization, capture, void and webhook event shows up in the per-purchase hash-chained ledger, and a direct UPDATE/DELETE on ledger rows fails
**Plans**: TBD
**Research flags**: v5 vs v6 AUTHORIZE button; `paypal-cert-url` and webhook-ID behavior on Render; which `PayPal-Mock-Response` codes work on capture/void; US Sandbox accounts from India. Day-1 manual checks: PayPal Sandbox app + Channel3 key in hand, Gemini quota in AI Studio, Devpost rules and sponsor pages.

### Phase 2: Promise Receipt
**Goal**: A buyer turns a natural-language instruction into an exact, hash-sealed Promise Receipt they approve, and the real Sandbox authorization is bound to that receipt hash
**Mode:** mvp
**Depends on**: Phase 1
**Requirements**: INTENT-01, INTENT-02, INTENT-03, DISC-01, DISC-02, DISC-03, RCPT-01, RCPT-02, RCPT-03, RCPT-04, PAY-08, UI-01
**Success Criteria** (what must be TRUE):
  1. In the Shopper Agent view, a buyer types an instruction ("new black over-ear headphones under $100, arrive within 5 days"), sees and edits typed constraints labeled AI or fallback, and completes this step even with every LLM key disabled. The deadline is resolved in code against the injected clock.
  2. The buyer sees real Channel3 candidates, picks an exact offer and variant, and gets a merchant quote labeled "Sandbox stand-in for <domain>". The raw Channel3 bytes are stored, `condition: null` shows as UNVERIFIED, and non-USD offers are rejected.
  3. The buyer approves a specific receipt hash before the PayPal button appears; approving a non-current hash returns 409, and the resulting PayPal order carries the receipt hash in `custom_id`
  4. A quote whose total exceeds the buyer's max is rejected before any PayPal call
  5. A merchant term change creates a new receipt version, marks the old one STALE and requires reapproval; approved receipts cannot be modified at the DB layer, and the golden hash vector plus the Postgres round-trip test pass
**Plans**: TBD
**UI hint**: yes
**Research flags**: Pick a demo headphone product with a `Color` variant and mixed-condition offers; confirm Channel3 plan limits, Gemini free quota, and current OpenRouter `:free` models with structured output.

### Phase 3: Drift-Gated Settlement + Promise Replay
**Goal**: Fulfillment evidence is checked deterministically against the approved receipt, and capture happens only on MATCH: refurbished leads to CAPTURE BLOCKED, then a seller correction plus carrier acceptance leads to a real capture, and all of it is visible in one Replay
**Mode:** mvp
**Depends on**: Phase 2
**Requirements**: PAY-02, PAY-07, FULF-01, FULF-02, DRIFT-01, DRIFT-02, DRIFT-03, DRIFT-04, LEDG-02, UI-02, UI-03, PROOF-01, SEC-02
**Success Criteria** (what must be TRUE):
  1. In the Sandbox, a judge uses the SYNTHETIC Scenario Console to send "refurbished" and sees CAPTURE BLOCKED with findings citing the invariant and evidence IDs. After "correct SKU + carrier accepted", the gate re-evaluates, a real `final_capture` capture reaches `COMPLETED`, and the webhook is recorded.
  2. Label-only shipments, late ETAs and low-trust merchant claims produce HOLD, never capture; advancing the demo clock past `expiration_time` shows RENEWAL_REQUIRED and capture is prohibited
  3. The Promise Receipt view shows frozen constraints, hash, version, the status pill (AUTHORIZED · NOT CAPTURED / CAPTURE BLOCKED / CAPTURED), evidence with trust-ladder badges, and a plain-language explanation for each finding (LLM or template fallback)
  4. Promise Replay shows all 10 steps from instruction to settlement on one screen, each with source, timestamp, PayPal ID and hash, with the divergence step highlighted; "Verify integrity" shows a check mark or the first broken link
  5. All 11 acceptance cases pass as automated tests, including a 2-thread capture race that produces one capture, the happy path at clock = 2026-12-20, and the prompt-injection test
**Plans**: TBD
**UI hint**: yes

### Phase 4: Control Tower, Proof & Judge Readiness
**Goal**: A judge with no keys can open the live URL, run a fresh demo scenario, inspect drift cases in the control tower, read measured proof, and find a complete submission (README, video, Devpost) before the deadline
**Mode:** mvp
**Depends on**: Phase 3
**Requirements**: UI-04, PROOF-02, PROOF-03, PROOF-04, SEC-01, SEC-03, DEPLOY-02, DEPLOY-03
**Success Criteria** (what must be TRUE):
  1. The Merchant Control Tower (AG Grid Community) lists drift cases with separate Authorization and Gate columns and an auth-expiry countdown, and an operator can reconcile or void with a reason from the grid
  2. "Run demo scenario" creates a fresh, clock-relative receipt and authorization every time. The Proof page reports detection, unsafe-capture prevention, false-block rate, decision latency, duplicate actions and expiry handling over 15-20 labeled scenarios, with numerator and denominator shown.
  3. The gate enforces that there is no public capture/void endpoint and no import path from LLM code to payments/settlement (import-linter); seed/reset needs a token, and LLM endpoints are rate-limited per IP and fall back gracefully
  4. Following only the README in a fresh incognito browser (live URL, Sandbox buyer credentials, Scenario Console guide, proves / does-not-prove table, AP2 v0.2 mapping, APIMatic log, OSS license), a judge completes the full workflow
  5. A demo video under 3:00 covering the 8 acts is recorded by Nov 10 and the Devpost submission is complete before Nov 12 12:00 PT. The deploy runs on sponsor credits and free tiers only, the prod DB is created or renewed so it does not expire before Dec 21, and a cold-start notice is shown.
**Plans**: TBD
**UI hint**: yes
**Cut order if behind**: Postman (v2) -> scenarios beyond 11 -> AP2 export polish -> live LLM extraction (keep fallback + DRIFT explain) -> webhook processing beyond verify+log. Never cut: authorize/capture/void, drift gate, receipt hash + approval, Replay, refurbished -> BLOCK -> correction -> CAPTURE, idempotency, live deploy.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Money Spine on a Public URL | 0/TBD | Not started | - |
| 2. Promise Receipt | 0/TBD | Not started | - |
| 3. Drift-Gated Settlement + Promise Replay | 0/TBD | Not started | - |
| 4. Control Tower, Proof & Judge Readiness | 0/TBD | Not started | - |
