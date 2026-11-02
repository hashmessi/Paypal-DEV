---
phase: quick-261102-qw1
plan: 01
status: complete
completed: 2026-11-02
commits: [3e66b12, 1c062ea, 217dc86]
requirements: [P1-COUNTERFACTUAL, P1-MCP-GATE, P1-OFFLINE-VERIFIER]
---

# Quick 261102-qw1: P1 slice Summary

Counterfactual loss-avoided (integer cents, labelled simulated), a 4-tool MCP agent gate with no money tools, and an in-browser receipt verifier backed by a shared canonicalization vector.

## Tasks

1. **Counterfactual** (3e66b12): `app/proof/counterfactual.py` (pure, TypeError on non-int). Wired into `run_proof` (per-scenario + `protected`), `console._promise` and `/tower` kpis (`loss_avoided_cents`, `loss_avoided_simulated`), and `ReplayData.counterfactual`. UI on Proof, Tower, Replay.
2. **MCP gate** (1c062ea): `app/mcp_server` (`python -m app.mcp_server`), `mcp==2.3.0`, README section.
3. **Offline verifier** (217dc86): `/verify` page, `verifyReceiptJson` in `hash.ts`, shared vector in `test_canonical_vector.py` and `hash.vector.test.mjs`.

## Open items resolved from code

- **mcp 2.x API**: `FastMCP` is removed; server is `from mcp.server.mcpserver import MCPServer`, `@mcp.tool()`, `mcp.run("stdio")`, `await mcp.list_tools()` (confirmed from installed package).
- **Simulated flag**: `get_gateway` chose FakeGateway when `PAYPAL_CLIENT_ID in ("test","sandbox_test") or DEMO_MODE`. Extracted to `gateway_is_simulated()` in `proof/counterfactual.py`; `deps.get_gateway` now calls it (single source of truth, behavior unchanged).
- **reevaluate_gate**: not used. `get_gate_verdict` reads the stored `GateEvaluationRecord` (outcome, findings, stored explanation). A subprocess test confirms importing the server loads no `app.payments`, `app.webhooks` or `app.api` modules.

## Verification (exact commands, all passed)

- `cd backend && python -m pytest tests/test_canonical_vector.py tests/test_counterfactual.py tests/test_mcp_gate.py tests/test_phase4.py -q` -> 20 passed
- `cd frontend && node --experimental-strip-types src/lib/hash.vector.test.mjs` -> `hash vector OK`
- `cd frontend && npm run build` (tsc -b + vite) -> built, no errors (only the pre-existing chunk-size warning)
- Ad hoc: real `GET /receipts/{id}` body from a temp SQLite DB through `verifyReceiptJson` in node -> match true; `total_cents+1` -> false; invalid JSON -> "Not valid JSON."
- `python -m app.mcp_server </dev/null` exits 0 (starts and stops cleanly).

## Deviations

- **[Rule 3]** Extra files beyond plan list: `backend/app/api/deps.py`, `backend/app/core/config.py` (new `FRONTEND_BASE_URL`, default `http://localhost:5173`), `frontend/src/lib/api.ts` (pass `counterfactual`/`protected` through the API mapping layer), `frontend/src/layout/Sidebar.tsx` and `Topbar.tsx` (nav link + title).
- `get_gate_verdict` returns the stored explanation rather than re-calling `generate_explanation` (the stored text came from it).
- `canonicalJson` skips the non-integer check inside `product_snapshot`, mirroring the backend's `assert_no_floats` exemption; a blanket throw would reject real receipts with float ratings.
- `sha256Hex` now throws without WebCrypto (was a fake non-crypto hash). This also affects `ShopPage`/`storage.ts` on non-secure origins (http non-localhost); Render is HTTPS.

## Known limits

- `compile_promise` only accepts offers from the demo catalog (`get_offer_by_id`), not live Channel3 results. It creates a `Purchase` row directly (no PayPal order), which is created later via the UI/checkout.
- Counterfactual `simulated` is a global gateway-mode flag, not per-purchase; the proof `protected` figure is always simulated (fixed-clock synthetic scenarios).
- Not exercised: UI visual check in a browser, MCP tool calls over a real stdio client, full backend test suite, `pip check` shows an unrelated pre-existing streamlit/pillow conflict in the global Python.
- `mcp` was installed into the global Python (tests run there); `backend/.venv` was not updated.
- Local `promiseloop.db` has a stale schema (`decision_events.id` missing) pre-existing; untouched.
- Hash drift edge cases (astral keys, integral floats in `product_snapshot`) documented as shortcuts in `hash.ts`.
