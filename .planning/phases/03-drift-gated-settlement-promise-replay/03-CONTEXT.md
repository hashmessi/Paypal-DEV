# Phase 03: Drift-Gated Settlement + Promise Replay — Context & Requirements Lock

**Phase:** 03-drift-gated-settlement-promise-replay  
**Goal:** Deliver deterministic invariant gate evaluation, fulfillment evidence ingestion, scenario console triggers, seller correction lifecycle, settlement gating, plain-language finding explanations, and 10-step Promise Replay audit.  
**Depends On:** Phase 01, Phase 02  

---

## 1. Requirements Lock

### Invariant Gate & Decision Outcomes (DRIFT-01, DRIFT-02, DRIFT-03, DRIFT-04)
- Deterministic Evaluation Function:
  `evaluate(receipt, auth, evidence_list, now: datetime) -> GateEvaluation`
  Pure deterministic logic with zero LLM dependence for the decision:
  - Outcome: `MATCH` | `DRIFT` | `HOLD` | `PROHIBITED`
  - Invariants:
    1. **INV-01 (Condition Invariant)**: If receipt requires `NEW`, but evidence condition is `REFURBISHED` or `UNVERIFIED` -> `DRIFT` (Severity: `BLOCKER`, Finding: "Condition drift: expected NEW, evidence shows REFURBISHED").
    2. **INV-02 (SKU/Variant Invariant)**: If evidence `sku` or `color` does not match expected SKU / color -> `DRIFT` (Severity: `BLOCKER`, Finding: "SKU mismatch: expected X, evidence shows Y").
    3. **INV-03 (Carrier Status Invariant)**: Carrier status must be `ACCEPTED` or beyond. `LABEL_CREATED` alone produces `HOLD` (never capture).
    4. **INV-04 (ETA Invariant)**: If carrier ETA exceeds promised delivery deadline -> `HOLD`.
    5. **INV-05 (Trust Ladder)**: Low-trust merchant claims alone cannot satisfy carrier invariants (can only cause HOLD).
    6. **INV-06 (Authorization Expiry - PAY-07)**: If `now >= auth.expiration_time` -> `PROHIBITED` (Status: `RENEWAL_REQUIRED`). Capture is prohibited.
- Settlement Gating (PAY-02):
  - System captures authorization (`final_capture: true`) **ONLY** when `gate.outcome == "MATCH"`.
  - If outcome is `DRIFT`, `HOLD`, or `PROHIBITED`, capture is rejected locally with typed error `CaptureBlockedByGateError` without calling PayPal.
- Re-evaluation on Evidence (DRIFT-02):
  - Every new evidence event re-evaluates the gate.
  - Seller correction pattern: Initial Refurbished evidence (`DRIFT` / `CAPTURE BLOCKED`) -> seller issues correction with matching SKU & carrier acceptance -> re-evaluates to `MATCH` -> capture reaches `COMPLETED`.
- Plain-Language Explanations (DRIFT-04, SEC-02):
  - Explanations generated from deterministic findings via template fallback or secondary LLM.
  - LLM never makes the gating decision and never sees untrusted raw seller text.

### Fulfillment Evidence Ingestion & Scenario Console (FULF-01, FULF-02)
- Ingest typed evidence:
  `sku`, `condition`, `color`, `carrier_status`, `eta`, `source`, `external_event_id`, `trust_level` ("CARRIER_TELEMETRY" | "MERCHANT_ATTESTATION"), `is_synthetic`.
- Deduplication:
  `UNIQUE(purchase_id, source, external_event_id)`. Re-delivering identical evidence returns duplicate status without duplicate event recording.
- Scenario Console (FULF-02):
  Supported synthetic triggers:
  1. `refurbished`: emits Refurbished condition evidence -> `CAPTURE BLOCKED`.
  2. `wrong_color`: emits wrong color evidence -> `CAPTURE BLOCKED`.
  3. `corrected`: emits matching SKU + carrier `ACCEPTED` -> re-evaluates to `MATCH`.
  4. `label_only`: emits carrier `LABEL_CREATED` -> `HOLD`.
  5. `late_eta`: emits ETA past deadline -> `HOLD`.
  6. `duplicate_event`: resends prior event -> deduplication.
  7. `price_change`: triggers merchant quote price increase -> STALE receipt.
  8. `advance_clock`: advances injectable clock past `expiration_time` -> `RENEWAL_REQUIRED`.

### Promise Replay & Verification (UI-03, LEDG-02)
- 10-step structured lifecycle replay:
  1. Buyer Instruction (`INSTRUCTION_SUBMITTED`)
  2. Constraints Extracted (`INTENT_EXTRACTED`)
  3. Candidate Selected (`PRODUCT_SELECTED`)
  4. Quote Confirmed (`QUOTE_CONFIRMED`)
  5. Receipt Compiled & Hashed (`RECEIPT_COMPILED`)
  6. Buyer Approved Receipt (`RECEIPT_APPROVED`)
  7. PayPal Hold Authorized (`FUNDS_AUTHORIZED`)
  8. Fulfillment Ingestion (`EVIDENCE_INGESTED`)
  9. Gate Decision (`GATE_EVALUATED` — divergence highlighted on DRIFT)
  10. Settlement Capture / Void (`FUNDS_CAPTURED` or `HOLD`)
- Verify integrity (LEDG-02): Cryptographic verification of SHA-256 chain from genesis, returns `intact: bool`, `event_count: int`, `broken_step: Optional[int]`.

### Acceptance Testing Suite (PROOF-01)
- 11 comprehensive automated tests covering all acceptance cases:
  1. Happy path: matching SKU + condition + carrier accepted -> MATCH -> capture COMPLETED.
  2. Refurbished: condition mismatch -> DRIFT (CAPTURE BLOCKED).
  3. Wrong color / wrong SKU -> DRIFT (CAPTURE BLOCKED).
  4. Label created only (no carrier acceptance) -> HOLD.
  5. Late ETA (carrier ETA exceeds promised deadline) -> HOLD.
  6. Low trust merchant note alone -> cannot promote to MATCH.
  7. Expiration past expiration_time -> PROHIBITED (RENEWAL_REQUIRED).
  8. Seller correction: Refurbished -> seller corrects SKU + carrier accepted -> transitions from CAPTURE BLOCKED to MATCH -> capture succeeds.
  9. 2-thread capture race condition: produces exactly 1 capture.
  10. Prompt injection test: prompt injection attempt in tracking note cannot override invariant rules (SEC-02).
  11. Happy path with fixed clock at 2026-12-20.

