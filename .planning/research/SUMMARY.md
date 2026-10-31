# Project Research Summary

**Project:** PromiseLoop
**Domain:** Promise-gated PayPal settlement for agentic commerce (authorize → verify fulfillment against a buyer-approved contract → capture or block); solo hackathon MVP
**Researched:** 2026-10-31
**Confidence:** MEDIUM-HIGH (PayPal/Channel3/Render/package versions from official docs/schemas = HIGH; Devpost rules & sponsor pages blocked (403), Gemini free quotas unpublished, AG Studio hackathon licensing unknown = UNVERIFIED)

## Executive Summary

PromiseLoop occupies a gap PayPal, AP2, Verifiable Intent and ACP all leave open: those protocols record what the human authorized and stop at checkout; PayPal provides the authorize/capture/void lifecycle; Shopify can already auto-capture "when the order is fulfilled." Nobody gates capture on **trust-graded fulfillment evidence matching the buyer-approved contract** — that sentence is the pitch and must be said in the first 20 seconds of the video. Plain "capture on fulfilled" is commodity; a hash-chained audit log and spend limits are already claimed by at least one cohort entry (Writ). So the settlement gate is the differentiator; the receipt and Replay are its proof.

Experts build this as a functional core with an imperative shell: a **pure drift engine** `evaluate(receipt, auth, evidence, now) → Decision` (no I/O, no clock, all rules run, worst severity wins), an **immutable canonical-JSON/SHA-256 receipt** versioned and anchored in PayPal's `custom_id`, an **append-only per-purchase hash-chained ledger** from which Replay, Control Tower and metrics are read, and a single **`settlement`** module — the only code that turns a decision into money — using claim (row lock + CAS) → commit → PayPal call with a persisted deterministic `PayPal-Request-Id` → record. Stack is deliberately boring: sync FastAPI + SQLAlchemy 2.1 + psycopg 3 + Postgres 17, httpx2 for direct REST to PayPal and Channel3, one `openai` client covering Gemini (primary) / OpenRouter (fallback) / deterministic fallback, React 19 / Vite 8 / Tailwind 4 + AG Grid Community for the tower, deployed as a Render Blueprint (static site + one web service + Postgres). No worker, no queue, no SDKs, no async.

The dominant risks are external and time-decaying, not algorithmic: (1) the Sandbox authorize flow requires a real buyer popup approval — the Nov 2 gate hinges on it; (2) the product doc's fixed "by Nov 5" demo date is past during recording and judging, silently breaking the capture act; (3) Render free Postgres expires ~30 days after creation — mid-judging (Dec 1–15, winners ~Dec 21); (4) free LLM tiers can collapse on camera; (5) AG Studio licensing can eat the schedule. Each has a cheap structural mitigation below; none justifies adding AI features. The doc's rule stands: if Sandbox authorize+capture isn't working by Nov 2, cut scope.

## Corrections to the Product Doc (roadmapper: treat as requirement changes)

| # | Doc says | Research says | Required change |
|---|---|---|---|
| 1 | Demo instruction "…by Nov 5" | In the past at recording (~Nov 10) and judging (Dec); happy path HOLDs forever under a real clock. LLMs also guess the wrong year. | **All demo dates clock-relative** ("arrive within 5 days", seeded `clock.today()+N`). LLM returns relative text; code resolves against the injected clock + explicit timezone. Acceptance test runs MATCH path with clock = 2026-12-20. No calendar dates in fixtures, README or video script. |
| 2 | "Refurbished → block" via Channel3 | Channel3 offer `condition` is `new`/`used`/`null`; `refurbished` deprecated (rejected as filter, coerced to null). Filters match products, not offers. | "No refurbished" = **selected offer** `condition == "new"`; `null` = UNVERIFIED, never NEW. Buyer selects an **offer** (product+domain+condition+variant), never `offers[0]`. Refurbished violation in the demo comes from the labeled fulfillment simulator. |
| 3 | Control tower on AG Grid / AG Studio | AG Studio 3.0 is commercial; deploy needs a licence (45-day trial from Nov 1 lapses ~Dec 16, before winners). Agent Framework is BYO-LLM, burns free quota. Hackathon key access UNVERIFIED. | **AG Grid Community 36.2 (MIT) is the P0 tower.** AG Studio = conditional P1 only if a deployable key covering Dec 21 is in hand by ~Nov 8, one-day timebox, agent behind read-only proxy with no money tools. Community features only. |
| 4 | Deployed on Render | Free Postgres expires 30d after creation (+14d grace, then deleted) → DB from ~Nov 1 dies ~Dec 1. Free web service sleeps after 15 min (~1 min cold start). Sandbox auths age out at 29 days. | Before recording (~Nov 9) move to paid Starter API (~$7/mo) + Basic Postgres (~$6/mo) through Dec 21 — **user's call (costs money)**. If staying free: create prod DB no earlier than Nov 8 and upgrade before Dec 1. **Every demo run creates a fresh receipt + authorization**; seeded tower rows read-only with honest auth status. |
| 5 | Webhooks signature-verified (implied in settlement) | Webhooks arrive late on cold Render, retry up to 3 days, and `PAYMENT.AUTHORIZATION.VOIDED` fires for expiry too. | **Webhooks never on the capture path.** Synchronous capture/void API response is financial truth; webhooks only confirm + record, never trigger capture. Reconcile (`GET` order/authorization) fills Replay if a webhook is late. |
| 6 | Postman is a sponsor tool | Postman has no prize category; prizes: AG Grid (largest), APIMatic, Bryntum, Channel3, Render credits. | Postman collection → **P2**, judge-reproduction aid only; secret vars with empty initial values; only example env committed. |
| 7 | Competitors PayPilot = discovery+checkout, Warden = agent payment audit | Real PayPilot is an invoices/refunds MCP operator; no PayPal-hackathon "Warden" found; **Writ** already claims signed spend mandates + tamper-evident audit chain. | Fix competitor copy; pitch post-checkout/pre-settlement gate, not spend limits or hash chains. |
| 8 | AP2 intent/cart mandate | AP2 v0.2 renamed to open/closed Checkout Mandate + Payment Mandate. | Use v0.2 names; alignment is doc + field mapping only, never SD-JWT/VC. |
| 9 | 8-act demo | Video must be **< 3:00** (aggregator, MEDIUM). | Script 8 acts to ~2:50; Replay carries the story on one screen; record by **Nov 10**. |
| 10 | "Void when unfulfillable" | Auto-void on drift kills Act 6 (seller correction → capture). | DRIFT → BLOCK + review. Void only on terminal conditions (cancel, OOS, buyer cancel), operator-triggered with reason code. |

## Conflicts Between Research Files — Resolved

| Topic | Conflict | Resolution |
|---|---|---|
| `PayPal-Request-Id` retention | STACK: 6h Orders / 45d capture-void; ARCHITECTURE: none published; PITFALLS: UNVERIFIED | **Never depend on PayPal remembering the key.** Five layers: inbound fulfillment dedup `(source, external_event_id)`; webhook dedup on verified `event_id`; purchase row lock + CAS `UPDATE … WHERE state='authorized'`; deterministic `uuid5("capture:{authorization_id}")` / `uuid5("void:{authorization_id}")` persisted at auth record time; `final_capture: true`. Terminal 422s → reconcile by GET, never blind retry. 200 and 201 both success; `409 PREVIOUS_REQUEST_IN_PROGRESS` → back off, same key. |
| Idempotency key shape | three variants | **`action:authorization_id`** — one auth has at most one capture regardless of receipt version; a reapproval raising the total needs a new order/auth anyway (`MAX_CAPTURE_AMOUNT_EXCEEDED`). |
| Webhook verification | STACK+PITFALLS: postback; ARCHITECTURE: self-verify | **Postback for MVP** (2 of 3; less crypto, no cert-URL SSRF surface). Splice **raw body bytes** into the verify request. Keep `verify()` behind one function. Acceptance #10 offline via mocked postback FAILURE; live by tampering a real Sandbox event (never simulator). Dedup row inserted **after** verification. |
| JS SDK version | STACK: v6 primary; PITFALLS: v5 | **v5 components for the Nov 2 gate** (documented authorize flow is v5; no official v6 authorize sample). Try v6 only if it works first time. Backend identical. |
| Migrations | Alembic vs single schema.sql | **Alembic** (`alembic upgrade head && uvicorn …`); deployed DB exists from day 1 and must survive. Append-only trigger in a migration. |
| HTTP / DB access | httpx + raw psycopg vs httpx2 + SQLAlchemy | **httpx2** everywhere (openai 3.x depends on it; `MockTransport` for tests); SQLAlchemy 2.1 sync Session, raw `text()` fine for CAS / `FOR UPDATE`. No respx / pytest-httpx. |
| Money | Decimal/strings vs minor units | Integer minor units in hashed canonical JSON; `NUMERIC(12,2)` + `CHAR(3)` in DB; `Decimal` in Python (Channel3 parsed with `parse_float=Decimal`); strings to PayPal (`"89.99"`). Canonicalizer **rejects floats**. USD only. Max-total comparator and scope (incl. tax+shipping) explicit on the receipt. |
| Hash storage | re-canonicalize vs store bytes | **Store canonical bytes next to the hash** + JSONB queryable copy; never hash `jsonb::text`; golden-vector + Postgres round-trip tests. |
| "held" as payment state | implied vs rejected | Payment state mirrors PayPal only (`created → approved → authorized → capturing → captured / capture_pending / voided / expired / failed`). **Gate status** (MATCH/DRIFT/HOLD + findings) is separate, read from latest decision. Expiry evaluated lazily from PayPal `expiration_time` + injected clock; no scheduler. |

## Key Findings

### Recommended Stack (details: STACK.md)

All **sync** (psycopg async incompatible with Windows default ProactorEventLoop; demo concurrency single-digit). **Direct REST**, no SDKs. **pip + venv**, not uv.

- **React 19.3 + Vite 8.3 (`react-ts`, TS ~7.0, oxlint) + Tailwind 4.3 (`@tailwindcss/vite`)** — no ESLint (typescript-eslint peers TS < 6.1), no `react-router-dom` (removed in v8); `react-router` 8.5 + `react-router/dom`.
- **TanStack Query 5** — 2s `refetchInterval` polling; no websockets.
- **@paypal/react-paypal-js 10.6** — v5 API for the gate.
- **ag-grid-react / ag-grid-community 36.2** (same exact version) — MIT.
- **FastAPI 0.162 (not `[standard]`) + uvicorn 0.54 + Pydantic 2.14 + pydantic-settings**.
- **SQLAlchemy 2.1 sync + psycopg[binary] 3.3 + Alembic 1.20 + Postgres 17**; normalize Render `postgresql://` → `postgresql+psycopg://`.
- **httpx2 2.16** for all outbound HTTP.
- **openai 3.42 (Python)** — one client, two `base_url`s: Gemini `gemini-3.5-flash-lite` primary → OpenRouter `nvidia/nemotron-3.5-super-vl:free` (`provider.require_parameters: true`) → deterministic parser. **Model IDs in env config** (free models churn).
- **Render Blueprint** — static site + Python web service + Postgres 17; pin `PYTHON_VERSION=3.12.10` (default now 3.14.8).
- **Dev only:** Docker `postgres:17`, APIMatic Context Plugin (`npx context-plugins install paypal`; keep dated contribution log for README), newman, import-linter, `tzdata`, `.gitattributes` (LF; machine has `core.autocrlf=true`).
- **Never in runtime:** PayPal Agent Toolkit / `@paypal/mcp` (gives LLM money tools; no auth capture/void anyway).

### Expected Features (details: FEATURES.md; prefixes INTENT, DISC, RCPT, PAY, FULF, DRIFT, UI, PROOF, DEPLOY, SEC)

**P0 table stakes:**
- PAY: Orders v2 `intent=AUTHORIZE` → buyer popup approval → server authorize; capture **only from engine on MATCH**; operator void on terminal conditions; payment state machine; idempotency layers; auth clock (3-day honor, 29-day validity, injectable); webhook verify + dedupe + log, off capture path.
- INTENT: NL → strict typed constraints, schema-validated, relative deadline resolution in code; buyer confirms/edits; visible "AI-extracted" vs "fallback" label.
- DISC: real Channel3 search; buyer picks exact **offer** + variant; raw response bytes stored as snapshot; `null` condition = UNVERIFIED; separate merchant quote (total incl. ship+tax, seller, promised delivery) labeled "Sandbox stand-in for <domain>".
- RCPT: canonical JSON → SHA-256, versioned, immutable; pre-auth rejection of over-limit; buyer approves exact hash (409 if not current); merchant term change → STALE → reapproval; `custom_id = purchase_id:receipt_hash`; `invoice_id` = purchase UUID or omitted.
- FULF: typed evidence (SKU, variant, condition, carrier `LABEL_CREATED` vs `ACCEPTED`, ETA) with source, ingestion sequence, trust_level, synthetic flag; **judge-operable Scenario Console** (SYNTHETIC) with one button per scenario.
- DRIFT: pure engine; re-evaluate on each evidence; `claim` evidence can only HOLD; LLM plain-language explanation of each deterministic finding (template fallback) — keeps AI meaningful after Act 1.
- UI: Shopper flow; Receipt view (status pill, trust badges); **Replay** (one screen, 10 steps, divergence highlighted, "Verify integrity"); Control Tower on AG Grid Community with separate Authorization vs Gate columns.
- SEC: no public capture/void endpoint; secrets server-side; untrusted text never a decision input; token-protected seed/reset; per-IP rate limit on LLM endpoints.
- PROOF/DEPLOY: 11 acceptance tests; metrics page (numerator/denominator shown); public HTTPS deploy day 1; live through Dec 21; fresh auth per demo run; zero-key README judge path; video < 3:00; "what this proves / does not prove" table.

**Differentiators (order):** P0-lite — contract-conformant capture framing (vs Shopify capture-on-fulfilled), AP2 v0.2 / Verifiable Intent field mapping, integrity button, trust-ladder badges, metrics page. P1-1 LLM evidence normalizer with monotonic safety + visible prompt-injection test; P1-2 tracking+SKU push to PayPal (`/v2/checkout/orders/{id}/track`); P1-3 Ed25519 receipt signature; P1-4 Channel3 product-subscription STALE trigger (plan access UNVERIFIED); P1-5 reauthorization; P1-6 AG Studio / Agent Framework (cut first); P1-7 partial refund.

**Defer:** real AP2/VC credentials, multi-item / partial capture / multi-merchant, accounts/login, real carriers, dispute automation, websockets, read-only MCP, preorders, LLM tool calls touching money, LLM confidence gating capture.

**Cut order if behind:** AG Studio → Postman → scenarios beyond 11 → Ed25519 / AP2 export button → live LLM extraction (keep DRIFT-explain) → webhook processing beyond verify+log.
**Never cut:** authorize→capture/void, drift gate, receipt hash + approval, Replay, refurbished→BLOCK→correction→CAPTURE path, idempotency, live deploy.

### Architecture Approach (details: ARCHITECTURE.md)

Modular monolith, one process, one DB, no worker. Dependencies point downward: `api → settlement → {receipts, payments, webhooks, fulfillment, intent, catalog} → {drift, ledger} → core`. "LLM interprets, code controls money" is **mechanically enforced** by import-linter `forbidden` contracts in `scripts/verify.d/` (transitive): `intent`, `catalog`, `drift` cannot reach `payments`/`settlement`/`webhooks`; `drift` cannot import I/O libs or the clock. Every state change locks the purchase row, which also holds the ledger chain head.

1. **`core/`** — config, `Clock` (System / Fixed / DemoOffset only when `DEMO_MODE=true`), canonical JSON + SHA-256 (rejects floats), DB session.
2. **`payments/`** — `PaymentGateway` protocol, `PayPalGateway` (httpx2, cached OAuth token), `FakeGateway` kept honest by a Sandbox contract test, transition table `apply(state, event) → new | NOOP | ILLEGAL`, request IDs persisted at authorization.
3. **`webhooks/`** — postback verify on raw body, dedup after verify, map to payment transition; synchronous in-request (PayPal retry is the queue); no BackgroundTasks for money.
4. **`ledger/`** — `append_event()` in caller's transaction, `verify_chain()`, Replay assembled on read via one `STEP_OF` mapping; trigger blocks UPDATE/DELETE; `occurred_at` (clock, hashed) vs `recorded_at` (DB wall clock).
5. **`intent/` + `catalog/` + `receipts/`** — LLM draft → pure `compile()` (REJECTED or DRAFT+hash) → buyer `APPROVED {hash}` → `ApprovedReceipt`, the only type `create_order()` accepts. Lifecycle DRAFT/APPROVED/STALE/SUPERSEDED/REJECTED.
6. **`fulfillment/`** — ingest + dedup + trust levels + synthetic simulator; "latest" = our ingestion sequence, never event timestamp.
7. **`drift/`** — pure rules: receipt_current, auth_window, product/variant/condition/merchant/substitution, amount, carrier_acceptance, delivery_eta, unverified_claims; outcome = max severity; all rules run.
8. **`settlement/`** — Tx A (lock → evaluate → record → CAS claim) → commit → HTTP capture → Tx B (apply result); plus `void` and `reconcile` (on demand + at startup for rows stuck in `capturing`).

### Critical Pitfalls (details: PITFALLS.md)

1. **Fixed calendar demo dates + LLM year guessing** → relative deadlines resolved in code against the injected clock; happy-path test at 2026-12-20.
2. **Assuming authorization is server-only** — `/authorize` needs popup approval by a Sandbox **personal** account, SDK intent matching order intent, orders created on click (6h + 6h window), one auth per order. Popup is Act 4; US/USD buyer+merchant pair; binary Nov 2 gate from the deployed URL.
3. **Fake idempotency** (random request IDs, 201-only success, terminal 422 treated as transient) → five layers, concurrent-capture test, `PayPal-Mock-Response` negatives.
4. **Non-reproducible / hollow hash** (JSONB rewrite, float vs Decimal, naive timestamps, Python vs JS canonicalization) → store canonical bytes, golden vectors, `custom_id` external anchor, say "tamper-evident" never "tamper-proof".
5. **Live-dependency collapse on camera/judging** (free LLM quotas, Render cold start, free DB expiry, Channel3 drift) → visible fallback chain + extraction cache keyed by instruction hash, labeled Channel3 fixture fallback (still one live search on camera), paid plan for judging window, record by Nov 10 in segments, never fake PayPal responses.

Also from scaffold onward: prompt injection (structured-field comparison only; LLM output only adds holds; injection acceptance test); overclaiming (no "escrow", "proves what shipped", chargeback claims, "AI verifies"); Windows→Linux (`.gitattributes`, `tzdata`, `forceConsistentCasingInFileNames`, `npm run build` in the gate); only `COMPLETED` captures count as settled (201 can be `PENDING`).

## Implications for Roadmap

Four coarse vertical phases, each ending in a demoable proof. Order follows the dependency chain: money spine → receipt that feeds it → gate that decides money → judge-facing surfaces. The pure drift engine has no deps and can be written while credentials/deploys are pending.

### Phase 1: Money Spine on a Public URL (Oct 31 – Nov 2, hard gate)
**Rationale:** Highest external risk (Sandbox app, buyer approval, public HTTPS for webhooks); everything else needs a real auth ID.
**Delivers:** repo scaffold (`.gitattributes`, harness `verify.sh`, Alembic, `core/` clock + canonicalizer); Render Blueprint deployed day 1 with `/healthz`; `payments/` (token, create AUTHORIZE order, authorize, capture, void, GET; FakeGateway; transition table; persisted request IDs; CAS claim); minimal approve page (v5 button); `/webhooks/paypal` subscribed, postback-verified, deduped; `ledger/` append + chain + trigger; day-1 checks (Channel3 curl, Gemini quota in AI Studio, Devpost rules & sponsor pages in a browser).
**Exit (binary):** from the Render URL: order created → popup approved → authorized → captured; second order authorized → voided; capture replay with same key returns same capture id; capture-after-void refused locally without calling PayPal; a real webhook verifies SUCCESS and is stored.
**Avoids:** pitfalls #2, #3, #4, #9 (skeleton), #14, #16.

### Phase 2: Promise Receipt — Instruction to Bound Authorization (Acts 1–4, ~Nov 3–4)
**Rationale:** Receipt is the input type for both `create_order` and the drift engine; its hash must exist before the order (`custom_id`).
**Delivers:** `intent/` (one OpenAI-compatible client, Gemini → OpenRouter → deterministic chain, extraction cache, source label, relative date resolution); `catalog/` (Channel3 search + `GET /v1/products/{id}`, explicit offer selection, raw-bytes snapshot, USD-only); labeled merchant quote simulator; `receipts/` `compile()` + lifecycle + hash approval (409 on stale); `create_order(ApprovedReceipt)` with `custom_id`; Shopper Agent view + Receipt view (capture conditions in plain words before the PayPal button).
**Exit:** buyer approves an exact contract hash and a real Sandbox auth is bound to it (`custom_id` visible); over-limit rejected before any PayPal call; merchant term change → STALE; Act 1 completes with LLM key disabled; golden hash vector + DB round-trip pass.
**Avoids:** pitfalls #1, #5, #6, #7, #8, #13 (extraction boundary).

### Phase 3: Drift-Gated Settlement + Promise Replay (Acts 5–8, ~Nov 5–8) — the core loop
**Rationale:** Needs receipt + money spine + ledger; contains the whole thesis, gets the most days.
**Delivers:** `fulfillment/` ingest + dedup + trust + SYNTHETIC Scenario Console; pure `drift/` engine + decision table; `settlement/` (Tx A / HTTP / Tx B, operator void with reason, reconcile); expiry via clock + labeled "advance demo clock"; webhook transitions (capture COMPLETED/PENDING, AUTHORIZATION.VOIDED); DRIFT-explain (LLM prose, template fallback); Replay API + view with integrity verification and divergence highlight; all **11 acceptance tests** (L0 pure + L1 Postgres + FakeGateway incl. 2-thread race → exactly one capture); injection test; scenario dataset v1.
**Exit:** on Sandbox: refurbished shipment → CAPTURE BLOCKED → seller correction + carrier-accepted → real capture → webhook recorded → Replay shows valid chain and divergence step; 11/11 pass, including with clock = Dec 20.
**Avoids:** pitfalls #3, #10, #12 (trust labels), #13.

### Phase 4: Control Tower, Proof & Judge Readiness (~Nov 9–12)
**Rationale:** UI and docs over existing endpoints, no new money logic; submission work is fixed-cost and must start before Nov 11.
**Delivers:** AG Grid Community tower (drift cases, Authorization vs Gate columns, auth-expiry countdown, Reconcile + operator-void, read-only seeded rows); `scripts/metrics.py` + Proof page (15–20 labeled scenarios); security pass (import-linter contracts in gate, secret scan, token-protected seed/reset, per-IP LLM rate limit); Render hardening + **paid-plan decision before recording** + "Run demo scenario" button creating a fresh clock-relative scenario; incognito README walkthrough; README (judge path, Sandbox buyer creds, proves/doesn't-prove table, AP2 v0.2 mapping, APIMatic contribution log, OSS licence); video < 3:00 **recorded by Nov 10**; Devpost copy; optional P2 Postman collection. P1 items (normalizer first) only if 11/11 pass and video is recorded.
**Exit:** full workflow from a fresh browser on the public URL using only the README; video uploaded; deploy stays live through Dec 21.
**Avoids:** pitfalls #9, #11, #12, #15.

### Phase Ordering Rationale
- Dependency chain from ARCHITECTURE/FEATURES: real auth id → `ApprovedReceipt` → evidence + engine + settlement → views over the ledger. Ledger lands in Phase 1 because Replay, tower and metrics are reads of it (later = rewrite).
- Each phase is vertical (UI + API + DB + external call), ending in a live demoable act, so a solo dev always has something shippable; the cut order applies within Phase 4 first.
- External-risk items front-loaded to day 1; time-decaying items (clock-relative dates, fresh auths, DB expiry, AG licence window) designed in Phases 2–3 and verified in Phase 4.

### Research Flags
- **Phase 1 needs a spike:** v5 vs v6 AUTHORIZE button; actual `paypal-cert-url` host and webhook-ID behavior on Render; `custom_id` propagation onto auth/capture webhook resources (LOW); which `PayPal-Mock-Response` codes work on capture/void/authorize (only `DUPLICATE_INVOICE_ID` confirmed); whether a scripted half-manual Sandbox approval suffices for the gateway contract test; US Sandbox account behavior from India.
- **Phase 2 light checks:** pick a demo headphone product with a `Color` variant and mixed-condition offers; confirm Channel3 key/plan limits, Gemini free quota, current OpenRouter `:free` models with structured outputs.
- **Phase 3 & 4:** standard patterns, skip research (only manual checks: AG Studio key if pursuing P1-6, live Render pricing).

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions live from npm/PyPI today; PayPal & Channel3 from official schemas. MEDIUM: v6 authorize flow, httpx2 youth, Blueprint `routes` syntax. UNVERIFIED: Gemini free quotas. |
| Features | MEDIUM | Competitor/protocol analysis from primary specs; rubric, video length, judging dates from aggregators (Devpost 403); cohort entries from snippets. |
| Architecture | HIGH | PayPal behavior from downloaded OpenAPI schemas; Postgres locking from official docs; standard payments patterns. |
| Pitfalls | MEDIUM-HIGH | PayPal/Render/Channel3 official; float/JSON/Decimal verified locally; free-tier LLM figures third-party; Devpost rules LOW. |

**Overall:** MEDIUM-HIGH — engineering plan solid; residual uncertainty is hackathon rules, sponsor perks and free quotas, resolvable only manually on day 1.

### Gaps to Address
- **Devpost rules & sponsor pages (403):** video length, licence, testing access, prize-count limit, sponsor criteria (does APIMatic require Server SDK? AG Studio key or Render credits available?). Open in a browser on day 1. If APIMatic requires the SDK, switch `payments` internals to `paypal-server-sdk` 2.4 and keep webhooks on REST.
- **PayPal-Request-Id retention:** handled by design.
- **Sandbox expiry enforcement** can't be fast-forwarded → injectable clock + `PayPal-Mock-Response: AUTHORIZATION_EXPIRED`.
- **Reauthorization count** contradictory in PayPal docs — P1 only.
- **Gemini free quota** unpublished — check AI Studio day 1. $10 OpenRouter credits (50 → 1,000 RPD) is cheap insurance — **user decision (paid)**.
- **Render paid plan for judging (~$13–26 total)** — **user decision**, before ~Nov 9 recording and Dec 1 DB expiry.
- **Channel3 product subscriptions** (P1-4) — plan access unverified.
- **Willingness to pay** unvalidated — don't claim it.

## Sources

### Primary (HIGH)
- PayPal Orders v2 / Payments v2 / Webhooks v1 OpenAPI schemas; [authorize & capture later](https://developer.paypal.com/docs/checkout/standard/customize/authorization/); [Idempotency](https://developer.paypal.com/api/rest/reference/idempotency/); [Webhooks](https://developer.paypal.com/api/rest/webhooks/rest/); [Event names](https://developer.paypal.com/api/rest/webhooks/event-names/); [Negative testing](https://developer.paypal.com/tools/sandbox/negative-testing/request-headers/); [Agent Toolkit tools](https://paypal.gitbook.com/agent-toolkit-and-mcp-server/available-tools.md); [Hackathon blog](https://developer.paypal.com/community/blog/PayPal_AI_Hackathon)
- Channel3 OpenAPI spec + guides (offer, variant, caching, checkout "coming soon", rate limits, pricing)
- [Render free tier](https://render.com/docs/free); [Blueprint spec](https://render.com/docs/blueprint-spec); [free Postgres 30-day expiry](https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90)
- AG Grid React v36.2 quick start; AG Studio licence / AI quickstart / enterprise-licence scope pages
- [AP2 spec v0.2](https://ap2-protocol.org/ap2/specification/); [Verifiable Intent](https://verifiableintent.dev/); [Shopify payment authorization](https://help.shopify.com/en/manual/payments/payment-authorization)
- Gemini OpenAI-compat / structured output / terms; OpenRouter limits & structured outputs; [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html); [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785); [psycopg async on Windows](https://www.psycopg.org/psycopg3/docs/advanced/async.html); [import-linter forbidden contracts](https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/)
- npm/PyPI registries (2026-10-31) for all version pins

### Secondary (MEDIUM)
- [PayPal v4/v5 → v6 migration](https://developer.paypal.com/v4-v6); Render pricing (search-indexed); [Internshala listing](https://internshala.com/competitions/?p=13021); [PayPilot README](https://glama.ai/mcp/servers/fernandogarzaaa/paypilot/tree); Writ Devpost snippet

### Tertiary (LOW)
- [AI Plug Gemini free-tier measurement](https://aiplug.work/en/blog/gemini-free-tier-limits); OpenRouter free-model churn reports; `custom_id` propagation onto webhook resources; `paypal-cert-url` host; India-region Sandbox behavior

---
*Research completed: 2026-10-31*
*Ready for roadmap: yes*
