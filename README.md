# PromiseLoop

Promise-gated payments for agentic commerce. A buyer's instruction is compiled into a hash-sealed **Promise Receipt**, bound to a PayPal Sandbox authorization, and a deterministic **Promise Drift Engine** decides whether fulfillment evidence permits capture. **Promise Replay** reconstructs the whole lifecycle in one audit timeline.

> The LLM interprets text. Deterministic code controls money. Any drift blocks capture.

## Try it in 5 minutes (no keys needed)

> Cold start: the free Render instance sleeps after 15 minutes idle. The first load can take about a minute; the app shows a banner while it wakes.

1. Open the live URL: `<LIVE_URL — fill in after Render deploy>`
2. Go to **Control Tower** and press **Run demo scenario**. Every press creates a fresh receipt and authorization with dates relative to now. Nothing is pre-seeded.
3. Open the new case. In the **Scenario Console** press, in order:
   - `Refurbished` → gate shows **CAPTURE BLOCKED** (condition drift, INV-01).
   - `Corrected` → seller ships the exact SKU, carrier accepts → gate returns to **MATCH**.
   - Capture now succeeds. Capturing earlier is refused locally with no PayPal call.
4. Open **Replay** for the case: 10 steps from instruction to settlement, the divergence step highlighted, ledger hash-chain verified.
5. Open **Proof**: 6 metrics computed live from 18 labeled scenarios, each with numerator and denominator.
6. Optional real PayPal path: authorize with the Sandbox buyer `<SANDBOX_BUYER_EMAIL / PASSWORD — fill in>`.

### Scenario Console guide

| Button | Evidence injected | Expected gate |
|---|---|---|
| Refurbished | carrier ACCEPTED, condition REFURBISHED | DRIFT, capture blocked |
| Wrong color | carrier ACCEPTED, silver instead of black | DRIFT, capture blocked |
| Corrected | exact SKU + carrier ACCEPTED | MATCH, capture allowed |
| Label only | LABEL_CREATED, no carrier acceptance | HOLD |
| Late ETA | carrier ETA past the promised deadline | HOLD |
| Duplicate event | repeat of a prior event | deduplicated, no change |
| Price change | merchant quote shifts | receipt marked STALE, new version needs approval |
| Advance clock | clock moved past authorization expiry | PROHIBITED (renewal required) |

## What this proves and does not prove

| Proves | Does not prove |
|---|---|
| The gate refuses capture on every labeled drift/hold/expiry case (see Proof page, with denominators) | Real-world carrier or merchant data quality: evidence in the demo is synthetic and labeled so |
| Capture is idempotent: repeated capture attempts yield one capture | That the labeled suite covers every real drift; it is 18 hand-labeled cases, not a field study |
| An LLM-facing module has no import path to payment code (enforced by a test) | Production readiness: PayPal Sandbox only, single instance, in-memory rate limit |
| The ledger is hash-chained and tampering is detected | Merchant identity: the quote is a Sandbox stand-in labeled as such |
| Receipt hash is bound to the PayPal order (`custom_id`) | Legal or regulatory compliance of any kind |

## AP2 alignment (conceptual, not a conformance claim)

| PromiseLoop | AP2 idea | Note |
|---|---|---|
| Promise Receipt (hash-sealed, buyer-approved) | A signed, user-approved purchase mandate | We seal with SHA-256 over RFC 8785 JSON; no verifiable-credential signing |
| Gate decision + Replay | Auditable evidence that execution matched the mandate | |
| Not implemented | Verifiable credentials, agent identity, cryptographic signatures | Out of scope for the MVP |

The AP2 v0.2 field-level mapping has **not** been checked against the spec yet; treat this table as a sketch.

## APIMatic contribution log

Not yet used. `<fill in once the APIMatic PayPal Context Plugin has been run: what it was used for and what changed>`

## Agent MCP gate (no money tools)

An MCP server lets an AI agent search offers and *propose* a Promise Receipt, then read the gate verdict and replay. It exposes exactly four tools: `search_offers`, `compile_promise`, `get_gate_verdict`, `get_replay`. **There are no money tools**: no authorize, capture, void, reconcile or approve. `compile_promise` returns a draft receipt plus an `approval_url`; a human approves it in the UI. A test (`backend/tests/test_mcp_gate.py`) enforces the tool list and that the server never imports the payments, webhooks or API layers.

Run (stdio): `cd backend && python -m app.mcp_server`. Example client config:

```json
{ "mcpServers": { "promiseloop-gate": { "command": "python", "args": ["-m", "app.mcp_server"], "cwd": "backend" } } }
```

Set `FRONTEND_BASE_URL` (default `http://localhost:5173`) so approval links point at your UI.

## Architecture

React + Vite + TypeScript + Tailwind (AG Grid Community for the Control Tower) → FastAPI modular monolith → PostgreSQL. PayPal calls (create, authorize, capture, void) are server-side only; the browser sees only the public client ID.

```
backend/app/
  intent/      NL instruction -> typed constraints (LLM + deterministic fallback)
  discovery/   Channel3 candidates and merchant quote
  receipt/     canonical JSON, SHA-256 seal, approval gate
  payments/    PayPal port, state machine, idempotent capture/void
  drift/       pure deterministic gate (no LLM in the decision)
  fulfillment/ evidence ingestion, Scenario Console
  replay/      10-step lifecycle timeline
  ledger/      append-only hash chain
  proof/       labeled scenarios and measured metrics
```

## Run locally

```bash
# backend (Python 3.12)
cd backend && pip install -r requirements.txt
DEMO_MODE=true uvicorn app.main:app --reload     # SQLite + fake gateway, no keys

# frontend
cd frontend && npm install && npm run dev        # set VITE_API_URL=http://localhost:8000 to use the real API
```

Tests: `cd backend && python -m pytest -q`. Full gate: `bash scripts/verify.sh`.

## Configuration

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres in production, SQLite locally |
| `PAYPAL_CLIENT_ID` / `PAYPAL_CLIENT_SECRET` / `PAYPAL_WEBHOOK_ID` | Sandbox app credentials (server-side only) |
| `DEMO_MODE` | `true` uses a fake gateway when no real credentials are set |
| `ADMIN_TOKEN` | Required header `X-Admin-Token` for `/demo/scenarios` seeding. Empty disables it |
| `LLM_RATE_LIMIT_PER_MIN` | Per-IP limit on LLM-backed endpoints (default 10) |
| `GEMINI_API_KEY` / `OPENROUTER_API_KEY` / `CHANNEL3_API_KEY` | Optional; the app degrades to deterministic fallbacks without them |

## License

MIT, see [LICENSE](LICENSE).
