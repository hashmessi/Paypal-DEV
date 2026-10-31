# Stack Research

**Domain:** Promise-gated PayPal settlement for AI-initiated (agentic) commerce. Hackathon MVP, solo dev, deadline 2026-11-12 12:00 PT
**Researched:** 2026-10-31
**Confidence:** MEDIUM-HIGH overall. Package versions are HIGH (pulled live from the npm/PyPI registries today). PayPal REST is HIGH (official docs plus PayPal's generated SDK docs). Channel3 is HIGH (its own OpenAPI spec). The v6 JS SDK authorize flow is MEDIUM. AG Studio hackathon licensing and Gemini free-tier quotas are **UNVERIFIED**.

> **Devpost sponsor pages (`paypalaihackathon.devpost.com/details/*`) returned HTTP 403 to automated fetches.** Everything below comes from each vendor's own docs. Hackathon-specific perks (credits, licence keys, prize criteria) are **UNVERIFIED**. Open those 5 pages in a browser on day 1.

---

## Decisions at a glance

1. **Frontend:** the official Vite 8 `react-ts` template, unchanged (React 19.3, TypeScript 7.0, oxlint). Add Tailwind 4.3 via `@tailwindcss/vite`, React Router 8.5, TanStack Query 5, `@paypal/react-paypal-js` 10.6 (JS SDK v6 API), and AG Grid Community 36.2.
2. **Backend:** **sync** FastAPI 0.162, SQLAlchemy 2.1 (sync), psycopg 3.3, Alembic 1.20 and Pydantic 2.14. Use **httpx2** 2.16 for every outbound REST call and **openai** 3.42 as the single LLM client.
3. **PayPal:** **direct REST via httpx2** behind one `paypal` adapter module, not `paypal-server-sdk`. Verify webhooks with the postback API. Derive `PayPal-Request-Id` deterministically for every money call.
4. **Channel3:** **direct REST** for 2 endpoints. Store the raw JSON response as the product snapshot. Skip the SDK.
5. **LLM:** Gemini `gemini-3.5-flash-lite` (free tier, OpenAI-compatible endpoint) is primary. An OpenRouter `:free` model with structured outputs is the fallback. A deterministic rules parser is the last resort.
6. **Python env:** **pip + venv + pinned `requirements.txt`. Do not install uv.**
7. **Render:** one Blueprint with a static site, a free Python web service and free Postgres 17. Background workers are not free, so all processing runs in-process. Pin `PYTHON_VERSION=3.12.10`, because the Render default is now 3.14.8.

**Why sync over async:** psycopg's docs say it "is not compatible with the default ProactorEventLoop" on Windows, which is the dev box. Demo concurrency is single-digit. FastAPI already runs `def` endpoints in a threadpool. Sync code also means no pytest-asyncio and no event-loop policy hacks, so tests and the drift engine stay plain functions. The trade-off is lower throughput, which this MVP does not need.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|---|---|---|---|---|
| React | 19.3.1 | UI | Current stable. React Router 8 requires >=19.2.7. | HIGH |
| Vite | 8.3.5 | Dev server/bundler | Current stable (Rolldown-based). The official `react-ts` template pins it. Needs Node `^20.19 \|\| >=22.12` (local is 24.14.1). | HIGH |
| TypeScript | ~7.0.2 | Types | The official `create-vite` react-ts template now pins `~7.0.2` and uses oxlint. Keep the template default. | HIGH |
| Tailwind CSS | 4.3.3 (+ `@tailwindcss/vite` 4.3.3) | Styling | v4 has no `tailwind.config.js` and no PostCSS setup: add the `tailwindcss()` Vite plugin and `@import "tailwindcss";`. The plugin peer-supports Vite 8. | HIGH |
| React Router | 8.5.1 | Routing (4 to 5 views) | Current major (v8.0.0 shipped 2026-06-17). Use data mode: `createBrowserRouter` from `react-router`, and `RouterProvider` from **`react-router/dom`**. `react-router-dom` no longer exists. | HIGH |
| TanStack Query | 5.105.0 | Server state | `refetchInterval` polling is the simplest way to show authorization/capture/webhook state changing on the Receipt and Replay views without websockets. Mutations cover approve/authorize. | HIGH |
| @paypal/react-paypal-js | 10.6.1 (pulls `@paypal/paypal-js` ^11.3.0) | Buyer approval button | Official PayPal package. v10's default API is JS SDK **v6** (`@paypal/react-paypal-js/sdk-v6`). The legacy v5 components still ship in the same package as a fallback. | HIGH (package) / MEDIUM (v6 + AUTHORIZE flow, see below) |
| ag-grid-react + ag-grid-community | 36.2.0 | Merchant Promise Control Tower | Community is MIT and fine for production. v36 registers modules through `<AgGridProvider modules={[AllCommunityModule]}>`. This is the guaranteed P0 path. AG Studio is a conditional upgrade (see Integration Surfaces). | HIGH |
| Python | 3.12.10 (local) | Runtime | Already installed. Every pinned package supports it. Several require >=3.11 (SQLAlchemy 2.1, pydantic-settings, httpx2). | HIGH |
| FastAPI | 0.162.0 | HTTP API, modular monolith | Locked by the product doc. Current release. | HIGH |
| uvicorn[standard] | 0.54.0 | ASGI server | Standard FastAPI server. uvloop is skipped on Windows automatically. | HIGH |
| Pydantic | 2.14.2 | API schemas, LLM output validation, settings | FastAPI-native. It is also the validator for LLM structured output (`.parse()`), so one schema system covers API, LLM and receipt models. | HIGH |
| SQLAlchemy | 2.1.6 | ORM / Core | Typed `Mapped[]` models, JSONB, CHECK/UNIQUE constraints, `SELECT ... FOR UPDATE`. The append-only financial ledger needs all of these. Use sync `Session`. | HIGH |
| Alembic | 1.20.1 | Migrations | Versioned schema plus the append-only triggers. Run `alembic upgrade head` in the Render start command. | HIGH |
| psycopg (v3) | 3.3.6 (`psycopg[binary]`) | Postgres driver | Has a `cp312-win_amd64` binary wheel, so no compiler is needed. SQLAlchemy URL scheme is `postgresql+psycopg://`. | HIGH |
| PostgreSQL | 17 (Docker `postgres:17` locally, `postgresMajorVersion: "17"` on Render) | System of record | Locked by the product doc. Gives JSONB for raw Channel3/PayPal payloads and triggers to enforce append-only tables. Keep local and Render on the same major version. | HIGH |
| httpx2 | 2.16.0 | Outbound HTTP (PayPal, Channel3) | Pydantic's maintained continuation of httpx (first published 2026-05). `openai` 3.x already depends on it and does **not** install `httpx`. Starlette's `TestClient` now imports `httpx2` first. Using it for our own clients keeps **one** HTTP stack, and its built-in `httpx2.MockTransport` covers tests. | MEDIUM-HIGH (young library, but it is now the ecosystem default) |
| openai (Python) | 3.42.0 | One client for Gemini + OpenRouter | Both providers expose OpenAI-compatible Chat Completions with JSON-schema structured output. Two `OpenAI(base_url=...)` instances replace two SDKs. | HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| pydantic-settings | 2.16.2 | Typed env config (`PAYPAL_CLIENT_ID`, `CHANNEL3_API_KEY`, `DATABASE_URL`, ...) | Always. Fail fast on missing secrets at boot. |
| pytest | 9.2.0 | Acceptance suite (11 cases) + scenario dataset | Always. Use plain sync tests with FastAPI `TestClient`. |
| httpx2.MockTransport (built in) | ships with httpx2 | Mock PayPal/Channel3 in tests | Inject the transport into the adapter's `httpx2.Client`. No extra package needed. |
| httpx2-pytest | 2.0.0 | Fixture-style HTTP mocking for httpx2 | Optional. Add only if hand-written MockTransport handlers get repetitive. |
| hashlib / json / uuid / zlib (stdlib) | stdlib | Receipt SHA-256 over canonical JSON; deterministic `uuid5` idempotency keys | Always. No hashing or JCS library needed if money is stored as strings/`Decimal` (no floats). |
| oxlint | 1.90.0 (template pin ^1.89.0) | Frontend lint | Template default. Fast, and it works with TS 7. |
| @types/react, @types/react-dom | 19.3.0 | React types | Template default. |
| openapi-typescript | 7.13.0 | Generate TS types from FastAPI `/openapi.json` | Optional, dev-only. Worth it if API shapes churn. Skip if 10 hand-written types are enough. |
| ag-studio + ag-studio-react | 3.0.0 (**Commercial** licence) | AG Studio dashboard + Studio Agent Framework | **Only** with a deployable licence key in hand (AI-enabled if using the Agent Framework). See AG Studio section. |
| newman | 6.2.3 | Run the Postman collection headless | Run `npx newman run ...`. Judges need no Postman login. Optionally call it from `scripts/verify.d/`. |

### Development Tools

| Tool | Purpose | Notes |
|---|---|---|
| Docker `postgres:17` | Local DB | `docker run -d --name promiseloop-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=promiseloop -p 5432:5432 postgres:17` |
| PayPal Developer Dashboard (Sandbox) | REST app (client ID/secret), sandbox business + personal accounts, webhook registration | Day-1 blocker. Register the webhook URL on the **sandbox** app against the Render URL. |
| APIMatic PayPal Context Plugin | Current PayPal SDK/API context for the coding agent (MCP) | Install with `npx context-plugins install paypal` (npm `context-plugins` 0.12.0, repo `github.com/apimatic/context-plugins-installer`). Targets Claude Code, Cursor, VS Code and Codex. Whether it needs an account or key is unverified. |
| Postman + PayPal public workspace | Fork PayPal's Orders v2/Payments collections, then build the PromiseLoop collection + Sandbox environment | Commit the exported JSON under `postman/`. Store secrets as environment variables of type "secret". Never commit them. |
| Postman CLI (npm `postman-cli` 1.83.0, official) | Cloud-reported collection runs | Optional. Newman is enough for README and judges. |

---

## Integration Surfaces (verified)

### 1. PayPal: Orders v2 + Payments v2 + Webhooks (Sandbox base `https://api-m.sandbox.paypal.com`)

| Step | Call | Idempotency (`PayPal-Request-Id`) | Notes |
|---|---|---|---|
| Token | `POST /v1/oauth2/token` (Basic `client_id:secret`, `grant_type=client_credentials`) | n/a | Cache until `expires_in`. Server-side only. (Standard OAuth flow; MEDIUM, from training data plus every PayPal sample.) |
| Create order | `POST /v2/checkout/orders` with `"intent": "AUTHORIZE"` | Optional, keys stored **6 h** (max 108 chars) | Send amounts as **strings** (`"89.99"`). Put the receipt hash in `purchase_units[0].custom_id` (<=255 chars, invisible to payer) and the receipt ID in `invoice_id` (<=127, must be unique per merchant). Send `Prefer: return=representation`. |
| Buyer approval | Client-side v6 button | n/a | See the frontend snippet below. |
| Authorize | `POST /v2/checkout/orders/{id}/authorize` | Optional, **6 h** | Authorization is at `purchase_units[0].payments.authorizations[0]`. Store its `id`, `status`, `expiration_time` and raw JSON. |
| Read auth | `GET /v2/payments/authorizations/{id}` | n/a | Reconcile before any capture/void. Status enum: `CREATED, CAPTURED, PARTIALLY_CAPTURED, VOIDED, DENIED, PENDING`. |
| Capture | `POST /v2/payments/authorizations/{id}/capture` (`final_capture: true`) | **Send always**, keys stored **45 days** | A replay with the same key returns the latest status and does **not** capture twice. Two *simultaneous* calls with the same key: PayPal "processes the first and might fail the second" (409 "previous call in progress"). Serialize with a DB row lock. |
| Void | `POST /v2/payments/authorizations/{id}/void` | **Send always**, 45 days | Not allowed on a fully captured authorization. Default `return=minimal`, so ask for representation if you want a body. |
| Reauthorize (P1) | `POST /v2/payments/authorizations/{id}/reauthorize` | 45 days | Allowed only after the 3-day honor period and within 29 days. Returns a **new authorization ID** and restarts a 3-day honor period. In the US, up to 115% of the original amount and at most +$75. After 30 days, create a new authorization instead. |
| Refund (P1) | `POST /v2/payments/captures/{id}/refund` | 45 days | Post-capture remedy only. |
| Verify webhook | `POST /v1/notifications/verify-webhook-signature` | n/a | Send `transmission_id, transmission_time, cert_url, auth_algo, transmission_sig, webhook_id, webhook_event`. |

**Timing facts (HIGH, from the PayPal authorization guide):** 3-day honor period; 29-day validity; reauthorization as above. `PAYMENT.AUTHORIZATION.VOIDED` also fires when an authorization reaches its 30-day validity limit. Treat PayPal's `expiration_time` as the source of truth, and evaluate honor/expiry status with the injectable clock **at read/decision time**. No scheduler is needed.

**Webhooks (HIGH):**
- Subscribe to `CHECKOUT.ORDER.APPROVED`, `PAYMENT.AUTHORIZATION.CREATED`, `PAYMENT.AUTHORIZATION.VOIDED`, `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.PENDING`, `PAYMENT.CAPTURE.DECLINED` (the v2 name, not `DENIED`), `PAYMENT.CAPTURE.REFUNDED` and `PAYMENT.CAPTURE.REVERSED`.
- **Use postback verification**, and pass `webhook_event` **exactly as received**. PayPal warns that re-serialized JSON can fail verification. Build the request body by splicing the raw `await request.body()` bytes into the JSON string. Do not `json.loads` and then `json.dumps`.
- **Postback does not work for Webhook Simulator (mock) events.** Test with real sandbox events produced by our own authorize/capture/void flow. Self-verification (CRC32 of the raw body, plus a cert from `paypal-cert-url`, RSA-SHA256) is the documented alternative. Defer it to P1: it needs `cryptography` plus cert-host allowlisting to avoid SSRF.
- Delivery goes to HTTPS on port 443 and needs a 2xx response. PayPal retries **up to 25 times over 3 days**. Dedupe with a UNIQUE constraint on the PayPal event `id` in `webhook_events`.
- Negative tests: the sandbox supports the `PayPal-Mock-Response` header (negative-testing mode) on Payments calls. Use it in the Postman collection and the acceptance suite.

**Idempotency rule (opinionated):** `PayPal-Request-Id = uuid5(NS, f"{action}:{authorization_id}:{receipt_version}")`. Persist it **before** the HTTP call, so a crash-and-retry reuses the same key. Add a UNIQUE `(authorization_id, action)` on the financial-action table and take `SELECT ... FOR UPDATE` on the transaction row. Together these give exactly one capture across duplicate events, retries and races.

**Frontend (v6 SDK). MEDIUM: PayPal's v4/v5-to-v6 migration guide says intent moves into the server-side order body, but I found no official v6 *authorize* sample. Prove this in the Nov 1-2 spike.**
```tsx
import { PayPalProvider, PayPalOneTimePaymentButton } from "@paypal/react-paypal-js/sdk-v6";

<PayPalProvider clientId={import.meta.env.VITE_PAYPAL_CLIENT_ID} environment="sandbox"
                components={["paypal-payments"]} pageType="checkout">
  <PayPalOneTimePaymentButton
    createOrder={async () => ({ orderId: await api.createAuthorizeOrder(receiptId) })} // server sets intent=AUTHORIZE
    onApprove={({ orderId }) => api.authorizeOrder(orderId)}  // MUST return the promise; server calls /authorize
  />
</PayPalProvider>
```
- In v6, `environment` is **required**: the client ID no longer selects the environment. The v5 `&intent=authorize` script parameter does not exist in v6.
- **Fallback if v6 misbehaves:** the same package's v5 API (`PayPalScriptProvider options={{ clientId, intent: "authorize" }}` + `PayPalButtons`). PayPal's authorize-and-capture-later guide is written against v5, and v5 requires the script `intent` to match the order intent.

**Server SDK verdict:** `paypal-server-sdk` 2.4.0 (2026-08-21) is real and current. It covers Orders, Payments, Vault, Transaction Search and Subscriptions, and exposes `paypal_request_id`, `prefer` and `paypal_mock_response`. It has **no Webhooks/notifications controller**, it is sync on `requests` via `apimatic-core`, and it returns model objects. **Use direct REST:** about 8 calls, one HTTP stack (httpx2), raw JSON straight into the append-only audit log, and one mock transport for tests. Switch the adapter internals to the SDK only if the APIMatic prize turns out to require SDK usage (see Variants).

**PayPal Agent Toolkit / MCP:** these exist. `@paypal/agent-toolkit` 1.11.0 (npm) and `paypal-agent-toolkit` 1.11.0 (PyPI) are the toolkits. `@paypal/mcp` 1.8.1 is the local MCP server. The hosted servers are `https://mcp.sandbox.paypal.com` and `https://mcp.paypal.com` (`/sse`, `/http`). **Keep them out of the runtime.** They hand money-moving tools to an LLM, which breaks the core invariant ("LLM interprets, deterministic code controls money"). Dev-time use only, for example inspecting sandbox orders from Claude Code. The P1 "read-only MCP for third-party agents" should be PromiseLoop's own read-only server.

### 2. Channel3: product data API (HIGH, from Channel3's OpenAPI spec at `channel3.mintlify.dev/docs/openapi/openapi.json`)

- **Base:** `https://api.trychannel3.com`. **Auth:** header `x-api-key: $CHANNEL3_API_KEY`. Anonymous calls work at lower limits.
- **Key:** sign up free (Google/GitHub/email, no card) and get the key at `trychannel3.com/dashboard`. The docs have moved: `docs.trychannel3.com` now redirects to `channel3.ai/docs`.
- **Endpoints to use:**
  - `POST /v1/search` costs 1 credit. Body: `query`, `limit` (default 20, **max 30**), `filters`, `config`, `page_token`. Up to 500 products via paging.
  - `GET /v1/products/{product_id}` is **free**. It hydrates variant `available` per option. The optional `website_ids` parameter pins the merchant.
  - `POST /v1/lookup` (by product URL) costs 1 credit.
- **Filters that matter:**
  - `price {min_price, max_price}`.
  - `conditions`: default `['new']`, which **also matches unknown condition**.
  - `availability`: default `['InStock']`, and offers with no data count as InStock.
  - `brand_ids`, `website_ids`, `attributes`.
  - `config.offer_refresh_timeout_ms` (2000-10000) live-checks offers against the merchant site.
- **Product shape:**
  - Top level: `id, title, description, brands[{id,name}], images, category, colors, structured_attributes, ratings`.
  - `offers[]`: `{url, domain, price{price, compare_at_price, currency}, availability: InStock|OutOfStock, condition: new|used|null, max_commission_rate, dimensions}`.
  - `variants`: `null` or `{options[{name, values[{label, exists, available, product_id, thumbnail_url}]}], selected[{name,label}]}`.
  - The merchant is identified by `domain`.
  - Docs conflict: the product guide shows `price {amount, currency}`, but the OpenAPI spec says `{price, compare_at_price, currency}`. Trust the spec, and store the raw JSON anyway.
- **Limits:** new keys start on the `default` plan: 10 req/s for search, 5 req/s for lookup, **10,000/day**. Over the limit you get `429` with `Retry-After: 5`. **1,000 free credits/month**, then $0.007/credit.
- **SDKs exist** (`channel3-sdk` 4.6.0 on PyPI, imported as `channel3_sdk`; `@channel3/sdk` 4.6.0 on npm). **Skip them.** The receipt must freeze the *raw* response, not parsed models, and the Python SDK pulls in `httpx` 0.x as a second HTTP stack.
- **Product consequences (feed these to FEATURES/PITFALLS):**
  - Channel3 cannot say "refurbished". Condition is only `new | used | null`, so "no refurbished" maps to the filter `conditions=['new']` and does not prove newness. The drift engine must treat `null` condition as *unverified*. The refurbished violation in the demo comes from the fulfillment simulator.
  - Variants are "not yet live on all products". Pre-select a demo headphone product that has a `Color` variant.
  - Offer price is not the checkout price. The separate merchant quote stays mandatory, as the product doc already says.

### 3. AG Grid / AG Studio / Studio Agent Framework

- **AG Grid 36.2.0:**
  - Community is MIT and fine for production. It covers sorting, filters, quick filter, custom cell renderers (status chips) and row selection. That is enough for an exception grid. **(HIGH)**
  - Enterprise features (row grouping, master-detail, set filter, integrated charts, AI Toolkit) need a licence. There is a 30-day trial.
  - The AG Grid MCP server (dev-time) is included in Community.
- **AG Studio exists (HIGH):**
  - Packages: `ag-studio` and `ag-studio-react` 3.0.0, licence **Commercial**, React ^17-^19. It is a dashboard builder.
  - It runs **locally without a licence**, with a watermark and console warnings.
  - **Production/deployed use needs a licence.** The 45-day trial is requested via a form, and pricing is a sales-quoted subscription. The key is passed via `<AgStudioProvider licenseKey=...>`.
- **Studio Agent Framework exists (HIGH):**
  - Wiring: `AgStudioModuleRegistry.registerModules([AgStudioAiModule])`, then `createAiHarness(api, { adapter })`, then `<AgStudio ai={ai} />`. It is bring-your-own-LLM.
  - **"AG Studio ships no adapters."** The only documented adapter is an *example* for the OpenAI **Responses** API, imported from `ag-studio-harness/example-shared/openaiAdapter`. That package is **not on npm**, so copy it from AG's examples.
  - The adapter must relay tool calls.
  - **AI features require a licence key that includes AI.**
  - It is aimed at *building dashboards*, not answering end-user data questions.
- **Fit with our LLMs:** Gemini's OpenAI-compatible endpoint documents Chat Completions, not the Responses API. Using the Agent Framework therefore means writing a Chat-Completions adapter plus a backend proxy. AG Studio's own docs warn against calling the LLM from the browser.
- **Hackathon licence access: UNVERIFIED** (Devpost page returned 403).
- **Recommendation:** build the Control Tower on **AG Grid Community** first. That alone meets the P0 "plain AG Grid exception grid" fallback. Upgrade to AG Studio only if a deployable key is in hand by about Nov 8. Add the Agent Framework only if that key includes AI. Keep the agent read-only, behind `/api/studio-llm`, with no money tools.

### 4. LLM: Gemini + OpenRouter free tiers through one `openai` client

| | Gemini (primary) | OpenRouter (fallback) |
|---|---|---|
| base_url | `https://generativelanguage.googleapis.com/v1beta/openai/` | `https://openrouter.ai/api/v1` |
| Structured output | Supported via `chat.completions.parse` with Pydantic. Function calling also supported. OpenAI-lib compatibility is **beta**, and unsupported params are silently ignored. | `response_format: {type: "json_schema", json_schema: {name, strict: true, schema}}`. Set `provider: {require_parameters: true}` so requests only route to endpoints that support it. A model without support returns an error. |
| Free models (today) | Free-of-charge per the pricing page: `gemini-3.8-flash`, `gemini-3.6-flash`, **`gemini-3.5-flash-lite`**, `gemini-3.1-flash-lite` (all stable). The 2.5 Flash models are limited to past users. | `:free` models with `structured_outputs` per the live `/api/v1/models` endpoint (2026-10-31): **`nvidia/nemotron-3.5-super-vl:free`**, `xingchen-agi/xing4.0-29b-a4b:free`, `dots-studio/dots-3-note-preview:free`, `liquid/lfm-2.5-2.6b:free`. The Gemma 4 `:free` variants support JSON mode only, not strict schemas. **This list churns, so the model ID must be env config.** |
| Free limits | **UNVERIFIED.** The official rate-limit page no longer publishes free-tier numbers and points to the AI Studio dashboard. Limits are per project, and RPD resets at midnight Pacific. | 20 RPM. **50 requests/day** if less than $10 of credits was ever purchased, 1,000/day otherwise. 429s carry `X-RateLimit-*` and `Retry-After`. `GET /api/v1/key` shows daily usage. |
| Data use | Free-tier content **is used to improve Google products**. Send only synthetic demo data. | Varies by provider. |

- **Primary: `gemini-3.5-flash-lite`.** It is stable, free and fast. Gemini 3 models cannot turn reasoning off, so the lite model keeps latency low for a 6-field extraction. Alternate: `gemini-3.8-flash` via env.
- **Fallback: `nvidia/nemotron-3.5-super-vl:free`** on OpenRouter.
- **Terminal fallback:** a deterministic rules/regex parser covering the demo instruction, so Act 1 survives any 429.
- Call `client.chat.completions.parse(model=..., messages=..., response_format=PurchaseConstraints)`. This is the GA path in openai 3.x. Gemini's docs show the `beta.` alias, which still exists. Set `max_retries=1` and `timeout=20` per client. On a validation or 429 failure, move down the chain; never loop.
- The LLM receives only the instruction and untrusted product text. It gets no tools and no credentials.

### 5. Render

**Free-tier facts (HIGH, render.com/docs/free):**

| Limit | Value | Consequence |
|---|---|---|
| Web service spin-down | After **15 min** idle, ~**1 min** cold start | The first PayPal webhook after idle may time out. PayPal retries (25x over 3 days), so the event eventually lands but not on demo time. A judge's first page load also takes ~1 min. Fix: keep-warm pings during judging (fits in 750 h/month for one service), or upgrade the API to the cheapest paid instance for judging week (price not verified). |
| Instance hours | 750 h/workspace/month | One always-on service is ~720 h. Don't run a second free web service 24/7. |
| Free Postgres | 1 GB, **expires 30 days after creation**, 14-day grace, then deleted. One per workspace, no backups. | A DB created ~Nov 1 expires ~Dec 1 and is deleted ~Dec 15. **Check the Devpost judging window.** If it runs past expiry, upgrade the DB before then. |
| Background workers / cron | **Not available on free** | No worker service. Process webhooks and drift evaluation in-request and evaluate expiry lazily. This matches the modular monolith anyway. |
| Disk | No persistent disk | Everything durable goes in Postgres, including evidence and raw payloads. |
| Free Key Value | In-memory, lost on restart | Don't use it. |
| `preDeployCommand` | Free-plan availability not confirmed | Run migrations in `startCommand` instead. |
| Python default | **3.14.8** for services created after 2026-10-12 | Set `PYTHON_VERSION=3.12.10` (env var needs the full patch version) to match local. |
| Node default | 24.22.1 | Fine (React Router needs >=22.22). Pin `NODE_VERSION` to the local version for parity. |
| uv | Used only if `uv.lock` is present | Irrelevant with pip. |
| Render Workflows | Public beta since 2026-04; free availability unverified | Skip for MVP. |

**Blueprint skeleton** (field names verified against the Blueprint spec. The `routes`/`fromService` example bodies were partially stripped from the fetched page, so validate with the Render dashboard's Blueprint validator):
```yaml
databases:
  - name: promiseloop-db
    plan: free
    databaseName: promiseloop
    user: promiseloop
    postgresMajorVersion: "17"

services:
  - type: web
    name: promiseloop-api
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /healthz
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.10
      - key: DATABASE_URL            # Render gives postgresql://...; rewrite to postgresql+psycopg:// in settings
        fromDatabase: { name: promiseloop-db, property: connectionString }
      - { key: PAYPAL_CLIENT_ID, sync: false }
      - { key: PAYPAL_CLIENT_SECRET, sync: false }
      - { key: PAYPAL_WEBHOOK_ID, sync: false }
      - { key: CHANNEL3_API_KEY, sync: false }
      - { key: GEMINI_API_KEY, sync: false }
      - { key: OPENROUTER_API_KEY, sync: false }
      - { key: FRONTEND_ORIGIN, sync: false }   # for CORS allowlist

  - type: web
    name: promiseloop-web
    runtime: static
    rootDir: frontend
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    routes:
      - { type: rewrite, source: /*, destination: /index.html }   # SPA deep links
    envVars:
      - { key: NODE_VERSION, value: 24.14.1 }
      - { key: VITE_API_BASE_URL, sync: false }
      - { key: VITE_PAYPAL_CLIENT_ID, sync: false }   # public by design; never put secrets in VITE_*
```
`sync: false` values are prompted **only on first Blueprint creation**. Later syncs ignore them.

### 6. APIMatic + Postman (minimal useful integration)

- **APIMatic PayPal Context Plugin:**
  - What it is: a beta MCP server (announced by PayPal on 2026-05-29) that gives coding agents current PayPal **Server SDK** context for .NET, Java, PHP, **Python**, Ruby and **TypeScript/JS**. Install with `npx context-plugins install paypal`.
  - **Minimal use:** install it in Claude Code before the Phase 1 PayPal spike. Use it while writing the adapter, webhook verification and Postman requests. Keep a short dated log of what it actually corrected or supplied, for the README sponsor section, which the product doc already requires.
  - *Tension:* the plugin is SDK-centred and we use direct REST. If the sponsor criteria (unverified) reward SDK usage, take the SDK variant below.
- **Postman:**
  - Fork PayPal's public workspace (`postman.com/paypal/paypal-public-api-workspace`; PayPal's Orders v2 guide links it as the source of current payloads). It includes error simulation for Orders/Payments.
  - **Minimal deliverable:** one `PromiseLoop` collection with 3 folders, plus one `PromiseLoop Sandbox` environment (client ID/secret as secret-type vars, base URLs, IDs captured by test scripts). Export both to `postman/`. Run them with `npx newman run`.
    1. *PayPal Sandbox*: token, create AUTHORIZE order, authorize, get auth, capture with `PayPal-Request-Id`, the **same capture replayed** (assert same capture ID), void, capture-after-void (expect 422), and `PayPal-Mock-Response` negatives.
    2. *PromiseLoop API*: instruction, search, receipt, approve, simulate fulfillment, evaluate, replay.
    3. *Webhook negatives*: a forged-signature POST, expected to be rejected.
  - Prize criteria: UNVERIFIED (Devpost 403).

---

## Installation

```bash
# ---------- Frontend (Git Bash, from repo root) ----------
npm create vite@latest frontend -- --template react-ts --no-interactive --no-immediate
cd frontend
npm install react-router@^8.5.1 @tanstack/react-query@^5.105.0 @paypal/react-paypal-js@^10.6.1 \
            ag-grid-react@^36.2.0 ag-grid-community@^36.2.0
npm install -D tailwindcss@^4.3.3 @tailwindcss/vite@^4.3.3
# vite.config.ts: plugins: [react(), tailwindcss()]   |   src/index.css: @import "tailwindcss";
# Only if an AG Studio licence is in hand:  npm install ag-studio@3.0.0 ag-studio-react@3.0.0

# ---------- Backend ----------
cd ../backend
py -3.12 -m venv .venv
source .venv/Scripts/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install fastapi==0.162.0 "uvicorn[standard]==0.54.0" pydantic==2.14.2 pydantic-settings==2.16.2 \
            sqlalchemy==2.1.6 alembic==1.20.1 "psycopg[binary]==3.3.6" httpx2==2.16.0 openai==3.42.0
pip install pytest==9.2.0              # put in requirements-dev.txt (first line: -r requirements.txt)
# requirements.txt = the exact top-level pins above (Render builds from it)

# ---------- Local DB ----------
docker run -d --name promiseloop-pg -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=promiseloop -p 5432:5432 postgres:17
# DATABASE_URL=postgresql+psycopg://postgres:dev@localhost:5432/promiseloop

# ---------- Sponsor dev tooling ----------
npx context-plugins install paypal     # APIMatic PayPal Context Plugin (MCP) into Claude Code
npx newman@6.2.3 run postman/PromiseLoop.postman_collection.json -e postman/PromiseLoop-Sandbox.postman_environment.json
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|---|---|---|
| pip + venv + pinned `requirements.txt` | **uv** 0.13.6 (Render supports it when `uv.lock` exists) | If dependency installs or Render builds become a bottleneck, or you want a transitive lockfile. For about 10 top-level deps over 12 days, a new tool earns nothing: pip is already installed and is Render's documented default. |
| SQLAlchemy 2.1 (sync) + separate Pydantic DTOs | SQLModel 0.0.48 (compatible with SA <2.2) | CRUD-heavy apps where one class per table is a win. Here, immutable receipts, append-only ledgers, JSONB and triggers need SQLAlchemy features anyway. One class serving as both table and API model also blurs the "frozen receipt vs. mutable DTO" boundary. SQLModel is still 0.0.x. |
| Sync SQLAlchemy/psycopg | Async (`create_async_engine`, psycopg async) | Real concurrency needs on Linux. On this Windows dev box, psycopg async needs a SelectorEventLoop workaround, and it buys nothing at demo scale. |
| httpx2 2.16 + `MockTransport` | httpx 0.28.1 + respx 0.23.1 / pytest-httpx 0.36.2 | If httpx2 shows a real bug. httpx last released 2024-12, and openai/Starlette have moved to httpx2. Adding httpx gives two HTTP stacks. |
| Direct PayPal REST | `paypal-server-sdk` 2.4.0 | If the APIMatic prize requires Server SDK usage (verify on the sponsor page). Keep REST for webhook verification either way, since the SDK has no webhooks controller. |
| Postback webhook verification | Self-verification (CRC32 + cert + RSA-SHA256) | If postback latency or availability bites, or you must verify simulator events offline. Needs `cryptography` and a cert-URL host allowlist (SSRF). |
| AG Grid Community 36.2 | AG Studio 3.0 (+ Agent Framework) | Only with a deployable (AI-enabled) licence key in hand by ~Nov 8 (see section 3). |
| TanStack Query | Plain `fetch` + `useEffect` | If you drop live status polling. It's not worth hand-rolling cache, retry and polling for the Receipt/Replay views. |
| React Router 8 | TanStack Router 1.170 | File-based typed routing for big apps. With 4-5 routes, it adds nothing here. |
| Gemini primary | OpenRouter primary | If AI Studio shows Gemini free quota below the demo plus judging needs. OpenRouter's 50 RPD (without $10 credits) is thinner. |
| oxlint (template default) | ESLint + typescript-eslint | Not with TS 7: `typescript-eslint` 8.72.1 peers `typescript <6.1.0`. Only if you downgrade to TS 6.0.3. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|---|---|---|
| `react-router-dom` | Removed in React Router v8. Agents trained on older code will reach for it. | `react-router` + `react-router/dom` (`RouterProvider`) |
| `typescript-eslint` / ESLint React template | Peer range `typescript <6.1.0` breaks against the template's TS 7.0.2 | oxlint (template default) |
| `PayPalScriptProvider` / `PayPalButtons` as the default | Legacy v5 API. v10's primary API is v6. | `@paypal/react-paypal-js/sdk-v6`; v5 only as the documented fallback |
| Expecting `&intent=authorize` in v6 | v6 has no script-level intent. Intent lives in the server's create-order body. | `"intent": "AUTHORIZE"` in `POST /v2/checkout/orders` |
| Calling PayPal or LLM APIs from the browser | Leaks secrets and breaks "deterministic code controls money" | Every PayPal/LLM call goes through FastAPI. The browser gets only the public client ID. |
| PayPal Agent Toolkit / `@paypal/mcp` in the runtime path | Gives an LLM tools that create or capture payments | Deterministic adapter. Toolkit/MCP for dev-time inspection only. |
| `respx`, `pytest-httpx` | They patch httpx 0.x only and won't intercept httpx2 clients | `httpx2.MockTransport` (or `httpx2-pytest`) |
| Channel3 SDKs | Parsed models aren't the raw snapshot the receipt must freeze. The Python SDK drags in httpx 0.x. | 2 direct REST calls; store the response JSON verbatim |
| Channel3 `offers[].price` as the charge amount | It's catalog data, not a checkout quote | Separate merchant quote record, approved in the receipt |
| Floats for money / in hashed JSON | Float formatting breaks canonical-JSON hash stability and drifts on totals | `Decimal` in Python, strings in JSON/PayPal (`"89.99"`), Postgres `NUMERIC(12,2)` |
| `json.loads` then `json.dumps` of webhook bodies before verification | PayPal explicitly warns this fails verification | Splice the raw request bytes into the verify payload |
| PayPal Webhook Simulator for postback-verification tests | Postback is unsupported for mock events | Real sandbox events from our own flow; unit-test the verifier with mocked PayPal responses |
| Celery / RQ / Redis / Render background worker | Workers aren't free on Render, Key Value is in-memory, and nothing here needs a queue | In-request processing + lazy expiry evaluation with the injectable clock |
| Local files for receipts/evidence | Free Render has no persistent disk | Postgres JSONB |
| `postgresql://` URL straight into SQLAlchemy | SQLAlchemy defaults that scheme to psycopg2, which isn't installed, so it crashes at boot | Normalize to `postgresql+psycopg://` in settings |
| `fastapi[standard]` | Pulls in the OpenTelemetry SDK/exporter, fastapi-cli, jinja2 and more, which lengthens Render builds for nothing | `fastapi` + `uvicorn[standard]` explicitly |
| `google-genai` (2.34.0) alongside `openai` | A second LLM SDK for the same job | `openai` with Gemini's OpenAI-compatible base URL |
| `tenacity`, `structlog` | openai has built-in retries. PayPal money calls must not be blindly retried. stdlib `logging` suffices. | Explicit single-retry with the same `PayPal-Request-Id` |
| Render Workflows | Public beta, free availability unverified, and not needed | In-process evaluation |

---

## Stack Patterns by Variant

**If the v6 button + AUTHORIZE flow fails in the Nov 1-2 spike:**
- Switch to the v5 components in the same package: `PayPalScriptProvider options={{ clientId, intent: "authorize" }}` + `PayPalButtons` (`createOrder`/`onApprove` calling the same backend).
- Because PayPal's authorize-and-capture-later guide is v5-based and documents exactly this. The backend is unchanged.

**If an AG Studio licence (with AI) is obtained:**
- Add `ag-studio` and `ag-studio-react` 3.0.0, and pass `licenseKey` on `AgStudioProvider`.
- Write a Chat-Completions adapter that posts to a backend `/api/studio-llm` proxy. The proxy reuses the same openai client chain and is read-only, with no money tools.
- Because the only shipped example adapter targets the OpenAI Responses API and calls the LLM from the browser.

**If the APIMatic sponsor criteria require Server SDK usage:**
- Implement the `paypal` adapter's Orders/Payments calls with `paypal-server-sdk` 2.4.0 (sync, compatible with the sync stack). Keep webhook verification on raw httpx2 REST.
- Because that is where the Context Plugin adds measurable value, and the SDK lacks webhooks.

**If the Gemini free quota (check AI Studio on day 1) is too low:**
- Swap the primary to OpenRouter, and cache the demo extraction keyed by instruction hash.
- Buying $10 of OpenRouter credits lifts free models from 50 to 1,000 RPD. That is a paid step, so it's the user's call.

**If the judging window extends past ~30 days after DB creation:**
- Upgrade the Render Postgres instance before expiry (the 14-day grace period then deletion is unrecoverable on free).

---

## Version Compatibility

| Package A | Compatible With | Notes |
|---|---|---|
| react-router@8.5.1 | react/react-dom >=19.2.7, Node >=22.22.0, Vite 7+ | ESM-only; `react-router-dom` removed |
| @vitejs/plugin-react@6.1.2 | vite ^8.0.0 | Template default |
| @tailwindcss/vite@4.3.3 | vite ^5.2 \|\| ^6 \|\| ^7 \|\| ^8 | |
| vite@8.3.5 | Node ^20.19.0 \|\| >=22.12.0 | Local 24.14.1; Render default 24.22.1 |
| typescript@7.0.2 | oxlint 1.9x | **Not** typescript-eslint 8.72.1 (needs TS <6.1.0) |
| @paypal/react-paypal-js@10.6.1 | react ^16.8-^19; `@paypal/paypal-js` ^11.3.0 | v6 API at `/sdk-v6`; v5 docs in `README-PAYPAL-JS-SDK-V5.md` |
| ag-grid-react@36.2.0 | ag-grid-community **36.2.0 (exact)**; react ^16.8-^19 | Keep both pinned to the same version |
| ag-studio-react@3.0.0 | react ^17-^19 | Commercial licence |
| openai@3.42.0 (Py) | httpx2 >=2.12,<3; pydantic >=1.10.13,<3 | Does **not** install `httpx`; uses the OS trust store (fine on Windows and Render Linux) |
| starlette (current, via fastapi 0.162.0) | httpx2 (preferred), httpx fallback | `TestClient` works with httpx2 installed via openai |
| sqlalchemy@2.1.6 | alembic 1.20.1 (needs SA >=2.0); psycopg 3.3.6 | URL scheme `postgresql+psycopg://` |
| sqlmodel@0.0.48 | SQLAlchemy >=2.0.14,<2.2 | Only if you overrule the SQLAlchemy choice |
| psycopg-binary@3.3.6 | CPython 3.12 win_amd64 wheel exists | No compiler needed on Windows |
| pydantic-settings@2.16.2, sqlalchemy@2.1.6, httpx2 | Python >=3.11 | 3.12 OK; Render's 3.14.8 default **must be overridden** |
| respx@0.23.1 / pytest-httpx@0.36.2 | httpx 0.x only | Don't use with httpx2 |
| channel3-sdk@4.6.0 | httpx >=0.21.2,<1; Python >=3.10,<4 | A reason to skip it |

---

## Sources

- npm registry (`npm view`, 2026-10-31): react, vite, typescript (dist-tags), tailwindcss, @tailwindcss/vite, react-router, @tanstack/react-query, @paypal/react-paypal-js, @paypal/paypal-js, ag-grid-*, ag-studio*, @channel3/sdk, typescript-eslint, newman, postman-cli, context-plugins, @paypal/agent-toolkit, @paypal/mcp. HIGH
- PyPI JSON API (2026-10-31): fastapi, starlette, pydantic, pydantic-settings, sqlalchemy, sqlmodel, alembic, psycopg, psycopg-binary wheels, httpx, httpx2, httpx2-pytest, openai, uvicorn, pytest, respx, pytest-httpx, paypal-server-sdk, paypal-agent-toolkit, channel3-sdk, google-genai, uv. HIGH
- [create-vite react-ts template package.json](https://raw.githubusercontent.com/vitejs/vite/main/packages/create-vite/template-react-ts/package.json): TS ~7.0.2, oxlint, Vite ^8.3.5. HIGH
- [React Router v8.0.0 changelog](https://github.com/remix-run/react-router/blob/main/CHANGELOG.md#v800): `react-router-dom` removed, Node/React baselines. HIGH
- [Tailwind v4 + Vite install](https://tailwindcss.com/docs/installation/using-vite). HIGH
- `@paypal/react-paypal-js` README (npm, v10.6.1): `PayPalProvider` / `PayPalOneTimePaymentButton` / `environment` required / v5 fallback. HIGH
- [PayPal: Authorize a payment and capture funds later](https://developer.paypal.com/docs/checkout/standard/customize/authorization/): honor period, 29 days, reauthorize, `intent=authorize` (v5). HIGH
- [PayPal v4/v5 to v6 migration](https://developer.paypal.com/v4-v6) (via search summary): intent in the order body; authorize server-side. MEDIUM
- [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/). HIGH
- [PayPal webhooks: verification](https://developer.paypal.com/api/rest/webhooks/rest/): postback vs self-verify, raw body, simulator limitation, 25 retries over 3 days. HIGH
- [PayPal webhook event names](https://developer.paypal.com/api/rest/webhooks/event-names/). HIGH
- [PayPal-Python-Server-SDK](https://github.com/paypal/PayPal-Python-Server-SDK) + its `doc/controllers/{orders,payments}.md` and `doc/models/*`: controllers, 6 h / 45 d key retention, `custom_id` <=255, `invoice_id` <=127, auth status enum, `expiration_time`, reauth limits. HIGH
- [PayPal MCP server](https://developer.paypal.com/tools/mcp-server/). HIGH
- [PayPal blog: Context Plugin for AI-assisted coding](https://developer.paypal.com/community/blog/A%20New%20Context%20Plugin%20for%20AI-Assisted%20Coding%20with%20PayPal%20SDKs) (2026-05-29); [APIMatic Context Plugins](https://www.apimatic.io/product/context-plugins). HIGH (existence and install command) / UNVERIFIED (account requirement)
- [PayPal Postman guide](https://developer.paypal.com/api/rest/postman/); [PayPal public Postman workspace](https://www.postman.com/paypal/paypal-public-api-workspace/collection/ujhlb45/paypal-apis). MEDIUM
- Channel3: [OpenAPI spec](https://channel3.mintlify.dev/docs/openapi/openapi.json) (parsed locally), [search guide](https://channel3.ai/docs/guides/search.md), [product guide](https://channel3.ai/docs/guides/product.md), [variants](https://channel3.mintlify.dev/docs/guides/variant.md), [rate limits](https://channel3.mintlify.dev/docs/faq/rate-limits.md), [pricing](https://channel3.mintlify.dev/docs/pricing.md), [quickstart](https://docs.trychannel3.com/quickstart). HIGH
- AG Grid: [React quick start v36.2](https://www.ag-grid.com/react-data-grid/getting-started/), [AG Studio AI quickstart](https://ag-grid.com/studio/react/ai-quickstart/), [AG Studio licence install](https://ag-grid.com/studio/react/licence-install.md), [licence pricing](https://ag-grid.com/studio/license-pricing.md), [AG Studio 3 blog](https://www.ag-grid.com/blog/ag-studio-3-is-here-dashboards-for-humans-and-ai/). HIGH (product/API) / UNVERIFIED (hackathon licence)
- Gemini: [OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai), [pricing (free tier column)](https://ai.google.dev/gemini-api/docs/pricing), [models](https://ai.google.dev/gemini-api/docs/models), [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) (no free numbers published). HIGH (features/models) / UNVERIFIED (quotas)
- OpenRouter: [limits](https://openrouter.ai/docs/api/reference/limits), [structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs), live `GET https://openrouter.ai/api/v1/models` (2026-10-31). HIGH (today's snapshot; volatile)
- openai-python: [v3.0.0 release](https://github.com/openai/openai-python/releases/tag/v3.0.0), [HTTPX2 migration guide](https://github.com/openai/openai-python/blob/main/httpx2.md), [helpers.md](https://github.com/openai/openai-python/blob/main/helpers.md). HIGH
- [HTTPX2 README](https://github.com/pydantic/httpx2); Starlette `testclient.py` imports (main). HIGH
- [psycopg async docs (Windows ProactorEventLoop)](https://www.psycopg.org/psycopg3/docs/advanced/async.html). HIGH
- Render: [free tier](https://render.com/docs/free), [Blueprint spec](https://render.com/docs/blueprint-spec), [Python version](https://render.com/docs/python-version), [Node version](https://render.com/docs/node-version), [Workflows announcement](https://render.com/blog/durability-as-code-introducing-render-workflows). HIGH (limits) / MEDIUM (exact `routes`/`fromService` YAML bodies)
- Devpost sponsor pages (channel3, aggrid, apimatic, postman, render): **HTTP 403, not read.**

---
*Stack research for: promise-gated PayPal settlement for agentic commerce*
*Researched: 2026-10-31*
