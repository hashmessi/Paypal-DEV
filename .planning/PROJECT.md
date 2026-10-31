# PromiseLoop

## What This Is

PromiseLoop is promise-gated payments for agentic commerce: the accountability layer that carries a buyer's original, human-approved purchase commitments all the way to PayPal settlement. It compiles a natural-language shopping instruction into a frozen, hash-sealed **Promise Receipt** (an Intent-to-Outcome Contract), binds it to a real Channel3 product snapshot, merchant quote and PayPal Sandbox authorization, and lets a deterministic **Promise Drift Engine** decide whether fulfillment evidence permits capture. **Promise Replay** reconstructs the whole lifecycle — instruction → product → contract → authorization → fulfillment → drift → settlement — in one audit timeline.

Built for the PayPal AI Hackathon (Devpost). Target users: operators of AI shopping platforms and merchants accepting AI-agent-initiated orders who need to know that "the exact item, price and agreed conditions were respected before I settle the payment."

## Core Value

**A PayPal authorization is captured only when deterministic checks prove the fulfillment evidence matches the buyer-approved Promise Receipt — any drift blocks capture.** The LLM interprets evidence; deterministic code controls money.

Promise-Gated Settlement + Promise Receipt + Promise Replay are the inseparable product core. Everything else serves those three or stays out of the MVP.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Intent & discovery**
- [ ] Buyer's natural-language instruction is extracted into strict typed constraints (product type, condition, variant/color, max total, delivery deadline, substitution allowed) via LLM with schema validation; the demo scenario has a deterministic fallback so a free-tier rate limit cannot break Act 1
- [ ] Real Channel3 product search returns candidates; the buyer picks the exact product + variant; the raw Channel3 response used is stored as the product snapshot (not an LLM summary)
- [ ] The merchant offer / full checkout total, seller and delivery promise are confirmed separately from Channel3 (Channel3 is not trusted for final checkout price)

**Promise Receipt**
- [ ] Promise Receipt compiler freezes intent constraints + product snapshot + merchant promise into a versioned contract with a tamper-evident hash
- [ ] Buyer reviews and approves the exact contract (product, total, merchant, delivery terms, capture conditions) before any money moves
- [ ] A contract whose total exceeds the buyer's authorized max is rejected before authorization
- [ ] If the merchant changes promised terms, the receipt becomes stale and buyer reapproval is required
- [ ] AI cannot modify approved constraints after approval (decision integrity)

**PayPal settlement**
- [ ] Real PayPal Sandbox order created with Orders v2 `intent=AUTHORIZE`; order ID and authorization ID stored
- [ ] Capture via `POST /v2/payments/authorizations/{id}/capture` only when every capture condition passes
- [ ] Void via `POST /v2/payments/authorizations/{id}/void` when the order is unfulfillable; a voided authorization is never captured
- [ ] All capture/void calls are idempotent (PayPal-Request-Id); the same event delivered twice yields exactly one financial action
- [ ] PayPal webhooks are signature-verified and deduplicated; invalid signatures are rejected
- [ ] Authorization timing (3-day honor period, 29-day validity) is tracked with an injectable clock; an expired authorization is never captured and escalates to a renewal workflow

**Fulfillment & drift**
- [ ] Merchant fulfillment adapter accepts order line / SKU / condition / variant events plus a carrier-accepted shipping event, each recorded with source, timestamp and trust level
- [ ] Fulfillment simulator, clearly labeled synthetic, drives the demo scenarios
- [ ] Promise Drift Engine deterministically compares intent, commercial, financial and fulfillment state and enforces the invariants: product, spending, merchant, promise, evidence, financial, execution, decision integrity
- [ ] Drift outcomes: MATCH → capture; DRIFT → block capture + review; missing carrier event → hold; ETA past deadline → hold for review/void
- [ ] Verified mismatch is distinguished from an unverified allegation (merchant claims are lower-trust evidence)

**Interfaces**
- [ ] Shopper Agent view: instruction, product selection, purchase approval
- [ ] Promise Receipt view: frozen constraints, payment authorization, evidence
- [ ] Promise Replay: one-click audit timeline of the full 10-step lifecycle showing exactly where the purchase diverged
- [ ] Merchant Promise Control Tower: drift cases, fulfillment events, authorization status, capture decisions — built on AG Grid / AG Studio (fallback: plain AG Grid exception grid)

**Proof & delivery**
- [ ] Acceptance suite passes all 11 cases from the product doc (exact match → capture; wrong variant → block; refurbished → block; over-limit → reject; changed terms → stale; missing carrier → hold; late ETA → hold; expired auth → prohibited; duplicate event → one capture; bad webhook signature → reject; already voided → no capture)
- [ ] Labeled dataset of ~15–20 scenarios reports detection, unsafe-capture prevention, false-block rate, decision latency, duplicate prevention, expiry handling
- [ ] Deployed on Render (frontend, FastAPI, Postgres) with a public webhook listener from early in the build
- [ ] Postman collection + Sandbox environment for authorize/capture/void/webhook and negative paths
- [ ] README with judge setup (Sandbox test accounts, required keys, how to run the demo), license, demo video, Devpost submission content

### Out of Scope

- Generic customer-support chatbot — competes with Gorgias; not the product thesis
- AI shopping marketplace — already demonstrated by other entries (Agentic Cart / PayPilot)
- Autonomous refund agent — the old, undifferentiated PromiseLoop concept
- Blockchain / token-based escrow — authorize-and-capture already supplies the financial lifecycle
- Multi-agent swarm — complexity without judging value
- Multi-merchant production onboarding — hackathon MVP uses one eligible Sandbox merchant flow
- Full logistics platform or CRM — AfterShip/Narvar territory
- Preorders / long-dated fulfillment — authorization may expire; MVP uses in-stock orders shippable within the honor period
- Elastic, KERNEL, Astropods, Bryntum, Zapier — sponsor-logo stacking, integration cost not justified
- Microservices — FastAPI modular monolith only
- Deferred to P1 (only after all P0 passes): partial refund after post-capture problem, authorization-expiry reauthorization execution, external carrier/merchant adapter, read-only MCP interface for third-party agents, additional fulfillment evidence formats

## Context

- **Source document:** `paypal.dev.product.md` (three-loop product hardening: senior developer, strategic analyst, hackathon judge). This PROJECT.md is synthesized from it plus initialization Q&A.
- **Hackathon:** PayPal AI Hackathon on Devpost. Five equally weighted judging criteria: technological implementation, design, potential impact, innovation, presentation. PayPal integration must be central. Projects can compete for applicable sponsor prizes (overall prize-count limit applies). Judges must be able to test from README instructions.
- **Sponsor tools chosen (purposeful, not stacking):** Channel3 (runtime product data), AG Grid AG Studio (control tower), APIMatic PayPal Context Plugin (dev-time integration help — document its actual contribution), Postman (API collection), Render (deployment). Channel3 + AG Grid deliver visible product value; APIMatic + Postman improve integration quality; Render delivers the live demo.
- **Competitive boundary:** Gorgias (support/returns), AfterShip (tracking/exceptions), Narvar (delivery promises/returns), Warden (agent payment permissions/audit), Agentic Cart / PayPilot (AI discovery + PayPal checkout). PromiseLoop owns verification *after checkout but before settlement*. We claim a product distinction, not an exclusive market.
- **PayPal facts relied on (verify in research):** Orders v2 supports `AUTHORIZE`; authorization holds funds without transferring them; honor period ~3 days, authorization valid up to 29 days with reauthorization; captured transactions require refund, not void. Authorization is not escrow.
- **Evidence boundaries (must be disclosed):** the carrier/fulfillment simulator is synthetic; merchant claims are lower-trust; a hash makes recorded history tamper-evident but cannot prove an externally supplied event is truthful; a receipt + carrier event is not proof of the physical goods in a package.
- **Dangerous assumptions to eliminate:** Channel3 price ≠ final checkout price; AI cannot know what physically shipped; a label ≠ carrier acceptance (require accepted/scan event); merchant claim ≠ proof; authorization ≠ escrow; AI never approves payments; not every merchant supports delayed capture.
- **Recommended demo (8 acts):** instruction ("new black over-ear headphones under $100, no refurbished, by Nov 5") → Channel3 discovery → Promise Receipt + hash → $89.99 authorized-not-captured → simulated fulfillment says refurbished → CAPTURE BLOCKED → seller corrects SKU + carrier-accepted event → capture executes and webhook recorded → full Replay.
- **Metrics:** contract-violation detection, unsafe-capture prevention, false-block rate, capture-decision latency, duplicate-action prevention, authorization-expiry handling. No real-world chargeback-reduction claims.
- **Market validation open:** strategic relevance is supported (PayPal's agentic-commerce discussion names post-purchase returns/disputes); willingness to pay is unvalidated.
- **Dev environment:** Windows 11, Node + npm, Python 3.12, Docker available; `uv` and `pnpm` not installed. Greenfield repo (only the product doc).

## Constraints

- **Timeline**: Submission deadline Nov 12, 2026 12:00 PM PT (Nov 13 01:30 IST) — fixed hackathon deadline
- **Timeline**: Hard checkpoint Nov 2 — one working Sandbox authorize + capture, or scope is cut immediately (never compensate with more AI features)
- **Team**: Solo developer + agents — roadmap must be lean and sequential-friendly
- **Credentials**: PayPal Sandbox app and Channel3 API key not yet confirmed in hand — obtaining them is a day-1 blocker
- **Tech stack**: React + Vite + TypeScript + Tailwind frontend; Python FastAPI modular monolith; PostgreSQL; Render — locked in product doc
- **AI provider**: Gemini API or OpenRouter free tiers — rate/quota limits mean strict schema validation, retries with backoff, and a deterministic fallback for the demo path; prefer one OpenAI-compatible adapter covering both
- **Security**: PayPal secrets server-side only; LLM receives no credentials and cannot create/capture/void payments; product descriptions and merchant messages are untrusted data (prompt-injection surface); approved constraints immutable by AI; idempotency on every capture/void
- **Payments**: PayPal Sandbox only; in-stock orders shippable within the authorization honor period
- **Webhooks**: require a public HTTPS endpoint — Render deploy or tunnel must exist early, not at the end
- **Data**: append-only financial and decision events; versioned receipts
- **Judging**: README must give judges everything needed to run and test (keys, Sandbox accounts, steps)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Promise-Gated Settlement (authorize → verify → conditional capture) instead of refund-after-the-fact | Money doesn't move until conditions pass; uses PayPal lifecycle as core state transitions | — Pending |
| LLM interprets, deterministic code controls money | Financial safety, testability, judge objection "why AI?" | — Pending |
| Promise Receipt hashed + versioned; merchant term change → stale + reapproval | Evidence integrity invariant | — Pending |
| FastAPI modular monolith + Postgres, no microservices | 12 days solo | — Pending |
| Gemini / OpenRouter free tier behind one OpenAI-compatible adapter with deterministic fallback | Free credits; free-tier rate limits must not break demo or judging | — Pending |
| Deploy to Render early (public webhook URL) rather than Nov 9–10 | Webhook verification can't be tested on localhost | — Pending |
| Injectable clock in drift engine | Authorization-expiry tests can't wait 3 days in Sandbox | — Pending |
| AG Studio control tower scheduled last among P0; fallback to plain AG Grid | Sponsor value, but not the core proof; solo time risk | — Pending |
| Five sponsor tools only (Channel3, AG Grid, APIMatic, Postman, Render) | Purposeful integrations over logo stacking | — Pending |
| Planning only at init — no scaffolding until Phase 1 | User choice | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-31 after initialization*
