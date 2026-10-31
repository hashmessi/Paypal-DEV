# Requirements: PromiseLoop

**Defined:** 2026-10-31
**Core Value:** A PayPal authorization is captured only when deterministic checks prove the fulfillment evidence matches the buyer-approved Promise Receipt — any drift blocks capture.

## v1 Requirements

### Payments (PAY)

- [ ] **PAY-01**: Buyer can approve a PayPal Sandbox order created with Orders v2 `intent=AUTHORIZE` in the PayPal popup (v5 JS SDK), and the server authorizes it and stores order ID, authorization ID and `expiration_time`
- [ ] **PAY-02**: System captures an authorization via `/v2/payments/authorizations/{id}/capture` with `final_capture: true` only when the drift engine returns MATCH; only `COMPLETED` counts as settled
- [ ] **PAY-03**: Operator can void an authorization with a reason code on terminal conditions (cancel, out of stock); a voided authorization is never captured (refused locally without calling PayPal)
- [ ] **PAY-04**: Payment state machine permits only legal transitions (`created → approved → authorized → capturing → captured / capture_pending / voided / expired / failed`)
- [ ] **PAY-05**: The same capture/void request delivered twice produces exactly one financial action (deterministic persisted `PayPal-Request-Id` = uuid5(action:authorization_id), row lock + CAS, `final_capture`, reconcile-by-GET on terminal errors)
- [ ] **PAY-06**: PayPal webhooks are postback-verified on the raw body, deduplicated by event ID after verification, and appended to the ledger; invalid signatures are rejected; webhooks never trigger capture
- [ ] **PAY-07**: Authorization honor period / expiry is evaluated from `expiration_time` and an injectable clock; an expired authorization is never captured and shows RENEWAL_REQUIRED
- [ ] **PAY-08**: Receipt hash is written into the PayPal order `custom_id`

### Intent (INTENT)

- [ ] **INTENT-01**: Buyer's natural-language instruction is extracted into strict typed constraints (product type, condition, color/variant, max total + currency, deliver-within, substitution allowed) via one OpenAI-compatible client (Gemini → OpenRouter free → deterministic fallback) with schema validation and an extraction cache
- [ ] **INTENT-02**: Delivery deadlines are relative and resolved in code against the injected clock (no LLM-resolved calendar dates)
- [ ] **INTENT-03**: Buyer can review and edit extracted constraints before search; UI labels whether they came from AI or the fallback

### Discovery (DISC)

- [ ] **DISC-01**: System runs a real Channel3 search from the constraints and shows candidates; buyer selects an exact offer + variant
- [ ] **DISC-02**: Raw Channel3 response bytes for the selected product are stored as the product snapshot; `condition: null` is treated as UNVERIFIED, never NEW; non-USD offers rejected
- [ ] **DISC-03**: A merchant quote (full total incl. ship+tax, seller, promised delivery) is confirmed separately and labeled "Sandbox stand-in for <domain>"

### Receipt (RCPT)

- [ ] **RCPT-01**: Receipt compiler freezes constraints + snapshot + quote + capture conditions into canonical JSON (money as integer minor units, floats rejected) → SHA-256, versioned, canonical bytes stored with the hash
- [ ] **RCPT-02**: A contract whose total exceeds the buyer's max is rejected before any PayPal call
- [ ] **RCPT-03**: Buyer approves the exact receipt hash (approve returns 409 if the hash is not current) before the PayPal button appears
- [ ] **RCPT-04**: A merchant term change creates a new version and marks the prior one STALE; reapproval is required; approved receipts are immutable at the DB layer

### Fulfillment (FULF)

- [ ] **FULF-01**: System ingests typed fulfillment evidence (SKU, variant, condition, carrier status LABEL_CREATED vs ACCEPTED, ETA) with source, ingestion sequence, trust level and synthetic flag, deduplicated by (source, external event id)
- [ ] **FULF-02**: Judge-operable Scenario Console (labeled SYNTHETIC) with one button per scenario: refurbished, wrong color, correct SKU + carrier accepted, label only, late ETA, duplicate event, merchant changes price, advance demo clock

### Drift Engine (DRIFT)

- [ ] **DRIFT-01**: Pure deterministic `evaluate(receipt, auth, evidence, now)` runs all invariant rules and returns MATCH / DRIFT / HOLD / PROHIBITED with findings citing the invariant and evidence IDs
- [ ] **DRIFT-02**: Every new evidence event re-evaluates the gate (block → correction → capture works end to end)
- [ ] **DRIFT-03**: Low-trust merchant claims can only cause HOLD; LABEL_CREATED never satisfies carrier ACCEPTED
- [ ] **DRIFT-04**: LLM writes a plain-language explanation of each deterministic finding (template fallback); it never decides and never sees raw merchant text

### Ledger (LEDG)

- [ ] **LEDG-01**: All business, financial and decision events are appended to a per-purchase hash-chained ledger; UPDATE/DELETE blocked by trigger
- [ ] **LEDG-02**: "Verify integrity" recomputes the chain and shows ✓ or the first broken link

### Interfaces (UI)

- [ ] **UI-01**: Shopper Agent view: instruction → constraints → candidates → quote → receipt approval → PayPal button
- [ ] **UI-02**: Promise Receipt view: frozen constraints, hash, version, status pill (AUTHORIZED · NOT CAPTURED / CAPTURE BLOCKED / CAPTURED), evidence list with trust-ladder badges
- [ ] **UI-03**: Promise Replay: one screen, 10-step timeline from instruction to settlement, divergence step highlighted, each step shows source, timestamp, PayPal ID and hash
- [ ] **UI-04**: Merchant Control Tower on AG Grid Community: drift cases, separate Authorization and Gate columns, auth-expiry countdown, reconcile and operator-void actions

### Security (SEC)

- [ ] **SEC-01**: No public capture/void endpoint; secrets server-side; LLM code has no import path to payments/settlement (import-linter contract in the gate)
- [ ] **SEC-02**: Product descriptions and merchant notes are untrusted data, never decision inputs; prompt-injection acceptance test passes
- [ ] **SEC-03**: Token-protected seed/reset; per-IP rate limit on LLM endpoints with fallback

### Proof (PROOF)

- [ ] **PROOF-01**: All 11 acceptance cases from the product doc pass as automated tests, including a 2-thread capture race → one capture and the happy path with clock = 2026-12-20
- [ ] **PROOF-02**: Proof page reports detection rate, unsafe-capture prevention, false-block rate, decision latency, duplicate actions, expiry handling from 15–20 labeled scenarios (numerator/denominator shown)
- [ ] **PROOF-03**: README gives judges a zero-key path (live URL, Sandbox buyer credentials, walkthrough, Scenario Console guide), a proves / does-not-prove table, AP2 v0.2 alignment mapping, APIMatic contribution log, OSS license
- [ ] **PROOF-04**: Demo video under 3:00 covering the 8 acts, recorded by Nov 10; Devpost submission complete before Nov 12 12:00 PT

### Deploy (DEPLOY)

- [ ] **DEPLOY-01**: Frontend, API and Postgres deployed on Render via Blueprint with a public HTTPS webhook URL from Phase 1
- [ ] **DEPLOY-02**: Deploy stays live through Dec 21 on sponsor credits + free tiers (prod DB created/renewed so it does not expire mid-judging; cold-start notice shown)
- [ ] **DEPLOY-03**: "Run demo scenario" creates a fresh, clock-relative receipt and authorization every time; no pre-seeded authorizations

## v2 Requirements (ordered — first after v1 passes)

- **V2-01**: LLM evidence normalizer for free-text merchant notes with monotonic safety (can only add holds) + visible prompt-injection demo
- **V2-02**: Push verified tracking + SKU to PayPal after capture (`/v2/checkout/orders/{id}/track`)
- **V2-03**: Ed25519 service signature over the receipt
- **V2-04**: Channel3 product-subscription trigger for STALE receipts
- **V2-05**: Reauthorization execution on expired authorizations
- **V2-06**: AG Studio / Agent Framework read-only NL query (only with a licence covering Dec 21)
- **V2-07**: Partial refund after a post-capture problem
- **V2-08**: Postman collection + Sandbox environment

## Out of Scope

| Feature | Reason |
|---------|--------|
| Customer-support chatbot, refund bot, dispute automation | Old concept; Gorgias / PayPal Agent Ready cover it |
| AI shopping marketplace | Already demonstrated by others; Channel3 search + buyer pick suffices |
| Capture/void via PayPal MCP / any LLM tool | Contradicts core value; toolkit lacks auth capture/void |
| LLM confidence gating capture | Non-deterministic, untestable |
| Auto-void on drift | Kills seller-correction act |
| Blockchain escrow, full AP2/VC credentials | Cost without demo value; specs are drafts |
| Accounts/login, multi-item carts, multi-merchant, preorders | Days of work, no judge value; auth expiry |
| Real carriers, websockets, microservices, workers | Infra cost; polling + labeled simulator suffice |
| Elastic, KERNEL, Astropods, Bryntum, Zapier | Sponsor-logo stacking |
| Paid LLM credits / paid Render plans | User choice: sponsor credits + free tiers only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PAY-01 | Phase 1 | Pending |
| PAY-02 | Phase 3 | Pending |
| PAY-03 | Phase 1 | Pending |
| PAY-04 | Phase 1 | Pending |
| PAY-05 | Phase 1 | Pending |
| PAY-06 | Phase 1 | Pending |
| PAY-07 | Phase 3 | Pending |
| PAY-08 | Phase 2 | Pending |
| INTENT-01 | Phase 2 | Pending |
| INTENT-02 | Phase 2 | Pending |
| INTENT-03 | Phase 2 | Pending |
| DISC-01 | Phase 2 | Pending |
| DISC-02 | Phase 2 | Pending |
| DISC-03 | Phase 2 | Pending |
| RCPT-01 | Phase 2 | Pending |
| RCPT-02 | Phase 2 | Pending |
| RCPT-03 | Phase 2 | Pending |
| RCPT-04 | Phase 2 | Pending |
| FULF-01 | Phase 3 | Pending |
| FULF-02 | Phase 3 | Pending |
| DRIFT-01 | Phase 3 | Pending |
| DRIFT-02 | Phase 3 | Pending |
| DRIFT-03 | Phase 3 | Pending |
| DRIFT-04 | Phase 3 | Pending |
| LEDG-01 | Phase 1 | Pending |
| LEDG-02 | Phase 3 | Pending |
| UI-01 | Phase 2 | Pending |
| UI-02 | Phase 3 | Pending |
| UI-03 | Phase 3 | Pending |
| UI-04 | Phase 4 | Pending |
| SEC-01 | Phase 4 | Pending |
| SEC-02 | Phase 3 | Pending |
| SEC-03 | Phase 4 | Pending |
| PROOF-01 | Phase 3 | Pending |
| PROOF-02 | Phase 4 | Pending |
| PROOF-03 | Phase 4 | Pending |
| PROOF-04 | Phase 4 | Pending |
| DEPLOY-01 | Phase 1 | Pending |
| DEPLOY-02 | Phase 4 | Pending |
| DEPLOY-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0

---
*Requirements defined: 2026-10-31*
*Last updated: 2026-11-01 after roadmap creation*
