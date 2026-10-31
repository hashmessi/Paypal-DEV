# Architecture Research

**Domain:** Promise-gated PayPal settlement for AI-initiated (agentic) commerce. FastAPI modular monolith + PostgreSQL + React, deployed on Render.
**Researched:** 2026-10-31
**Confidence:** HIGH for PayPal API behavior (checked against PayPal's published OpenAPI schemas for Payments v2, Orders v2 and Webhooks v1), Postgres locking semantics and Render limits (official docs). MEDIUM for the composition patterns (standard payments engineering, applied here). LOW items are flagged inline.

---

## Standard Architecture

### System Overview

One process, one database, no worker, no queue. Dependencies only point downward. The LLM sits in a leaf module that cannot reach the money layer, and import-linter enforces that.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ FRONTEND (React/Vite/TS/Tailwind, Render static site)                    │
│  Shopper Agent  │  Promise Receipt + Replay  │  Merchant Control Tower    │
└────────┬─────────────────────┬──────────────────────────┬────────────────┘
         │ JSON/HTTPS          │                          │
┌────────▼─────────────────────▼──────────────────────────▼────────────────┐
│ L1  api/  (thin FastAPI routers: validate input, open tx, call one svc)   │
│     shopper · receipts · checkout · fulfillment · webhooks · tower · replay│
├──────────────────────────────────────────────────────────────────────────┤
│ L2  settlement/  ("decision service": evaluate → gate → capture/void)     │
│     the ONLY module that calls drift.evaluate AND payments.capture/void   │
├──────────────────────────────────────────────────────────────────────────┤
│ L3  receipts/   payments/   webhooks/   fulfillment/   intent/   catalog/ │
│     (compiler,  (port, PayPal (verify,   (adapter,     (LLM +    (Channel3│
│      lifecycle)  client, fake, processor) simulator)    fallback) adapter)│
│                  state machine)                         ▲ leaf: no path   │
│                                                         │ to payments     │
├──────────────────────────────────────────────────────────────────────────┤
│ L4  drift/  (PURE: no IO, no DB, no clock)     ledger/ (append, chain,    │
│                                                         replay read)      │
├──────────────────────────────────────────────────────────────────────────┤
│ L5  core/  config · clock · canon (canonical JSON + sha256) · db · models │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
                   ┌────────────────▼─────────────────┐
                   │ PostgreSQL (9 tables, 1 trigger) │
                   └──────────────────────────────────┘
External: PayPal REST (Orders v2, Payments v2, Webhooks v1) · Channel3 · Gemini/OpenRouter
```

### Component Responsibilities

The eight modules named in the product doc, mapped to packages:

| Module (doc name) | Package | Owns | May import (internal) |
|---|---|---|---|
| Intent extraction | `intent/` | NL instruction → `IntentConstraints` *draft*, via the LLM with schema validation and a deterministic fallback. No DB, no tools/function-calling. | `core` only |
| Channel3 adapter | `catalog/` | Search, then return **raw response bytes** and parsed candidates. No LLM summaries. | `core` only |
| Promise Receipt compiler | `receipts/` | Pure `compile()` (constraints + snapshot + merchant promise → content + hash, or reject) plus the receipt lifecycle (draft/approved/stale/superseded). | `core`, `ledger` |
| Drift engine | `drift/` | Pure `evaluate(receipt, auth, evidence, now) → Decision`. | `core.models` only |
| PayPal adapter | `payments/` | `PaymentGateway` protocol, `PayPalGateway` (httpx), `FakeGateway`, the payment state machine, idempotency keys. | `core`, `ledger` |
| Fulfillment adapter | `fulfillment/` | Ingests order-line and carrier events (source, trust, `synthetic` flag, dedup). Includes the labeled simulator. | `core`, `ledger` |
| Webhook verification + processor | `webhooks/` | Pure signature verification, dedup, mapping a PayPal event to a payment transition. | `core`, `ledger`, `payments` |
| Audit + decision service | `ledger/` + `settlement/` | `ledger`: append-only hash-chained `decision_events`, chain verification, Replay assembly. `settlement`: orchestration that turns a decision into money movement. | `settlement` → everything in L3/L4 except `intent`/`catalog` |

**The one rule that makes "LLM interprets, code controls money" true:** `intent` output is never a receipt. It becomes binding only after `receipts.compile()` (deterministic validation) and a `BUYER_APPROVED` event that names the exact `content_hash`. `payments.create_order()` takes an `ApprovedReceipt`, which only `receipts.service.load_approved()` can construct. It reloads the receipt from the DB, checks `status='approved'` and re-verifies the hash.

### Mechanically enforced boundaries (import-linter, run in `scripts/verify.sh`)

import-linter `forbidden` contracts **check indirect (transitive) imports by default**. They can also forbid external packages when `include_external_packages = true` is set ([docs](https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/)). So "no path from the LLM to PayPal" becomes a failing build, not a convention.

```toml
[tool.importlinter]
root_package = "app"
include_external_packages = true

[[tool.importlinter.contracts]]
name = "LLM/catalog/drift have no path to money"
type = "forbidden"
source_modules = ["app.intent", "app.catalog", "app.drift"]
forbidden_modules = ["app.payments", "app.settlement", "app.webhooks"]

[[tool.importlinter.contracts]]
name = "Drift engine is pure"
type = "forbidden"
source_modules = ["app.drift"]
forbidden_modules = ["httpx", "psycopg", "sqlalchemy", "fastapi", "openai", "app.ledger", "app.core.db", "app.core.clock"]

[[tool.importlinter.contracts]]
name = "Layering"
type = "layers"
layers = ["app.api", "app.settlement", "app.receipts | app.payments | app.webhooks | app.fulfillment | app.intent | app.catalog", "app.drift | app.ledger", "app.core"]
```

(Check the exact `layers` syntax for independent siblings, `|`, against import-linter 2.x when scaffolding. The `forbidden` contracts are the load-bearing ones.)

## Recommended Project Structure

```
promiseloop/
├── backend/
│   ├── app/
│   │   ├── main.py                # app factory, router wiring, dependency providers (get_clock, get_gateway)
│   │   ├── core/
│   │   │   ├── config.py          # env settings (PAYPAL_*, WEBHOOK_ID, DEMO_MODE)
│   │   │   ├── clock.py           # Clock protocol, SystemClock, FixedClock, DemoOffsetClock
│   │   │   ├── canon.py           # canonical_json(), sha256_hex(); money as int minor units
│   │   │   ├── db.py              # connection pool, tx() context manager
│   │   │   └── models.py          # pydantic/dataclass domain types shared across modules
│   │   ├── intent/                # llm_client.py (OpenAI-compatible), extract.py, fallback.py
│   │   ├── catalog/               # channel3.py
│   │   ├── receipts/              # compiler.py (pure), service.py (lifecycle, stale/supersede)
│   │   ├── drift/                 # engine.py (evaluate), rules.py (one fn per invariant), remedies.py
│   │   ├── payments/              # port.py, paypal.py, fake.py, state.py (transition table), service.py
│   │   ├── fulfillment/           # service.py (ingest+dedup), simulator.py (SYNTHETIC)
│   │   ├── webhooks/              # verify.py (pure crypto), processor.py
│   │   ├── ledger/                # events.py (append_event, verify_chain), replay.py
│   │   ├── settlement/            # service.py (evaluate_and_settle, void, reconcile)
│   │   └── api/                   # one router per view/surface
│   ├── schema.sql                 # tables, constraints, append-only trigger
│   └── tests/
│       ├── drift/test_acceptance.py      # table-driven, pure
│       ├── scenarios/*.json              # 15–20 labeled scenarios (shared with metrics script)
│       ├── payments/test_gateway_contract.py  # same tests vs Fake (default) and Sandbox (-m sandbox)
│       ├── settlement/test_idempotency.py     # real Postgres + FakeGateway + FixedClock, threads
│       ├── webhooks/test_verify.py            # self-signed test cert, no network
│       └── ledger/test_chain.py               # tamper detection
├── frontend/                      # Vite React app (3 views)
├── scripts/verify.sh, scripts/verify.d/, scripts/metrics.py
├── postman/                       # collection + Sandbox environment
└── render.yaml
```

### Structure Rationale

- **One package per doc module.** The roadmap, the code and the judge narrative use the same names.
- **`drift/` and `receipts/compiler.py` are pure.** This is where 70% of the acceptance suite lives and it runs in milliseconds without Docker. Most bugs that matter are logic bugs, and they get caught here.
- **`settlement/` is the only orchestrator of money.** If a reviewer wants to know "what can move money?", the answer is two functions in one file plus the checkout router's create/authorize.
- **`ledger/` sits below the services.** Every service appends events through `append_event(conn, purchase_id, type, payload)`, so no service talks to another just to log.
- **Shortcut:** use a single `schema.sql` (drop and recreate in dev) instead of Alembic. Upgrade to migrations only if the deployed DB must survive schema changes after Nov 10.

---

## Architectural Patterns

### Pattern 1: Functional core, imperative shell (pure drift engine)

**What:** `drift.evaluate` takes plain immutable values and returns a `Decision`. It reads no DB, network or clock (`now` is a parameter). Each invariant is one small rule function returning findings. The outcome is the maximum severity across all findings (all rules run, no short-circuit), so Replay shows *every* problem, not just the first.

**When to use:** Always, for anything that decides whether money moves.
**Trade-offs:** The caller must load a consistent snapshot. `settlement` does this under the purchase lock (Pattern 4).

```python
# drift/engine.py
Severity = Literal["DRIFT", "HOLD", "INFO"]

@dataclass(frozen=True)
class Finding:
    code: str            # e.g. CONDITION_MISMATCH, CARRIER_ACCEPTANCE_MISSING, AUTH_EXPIRED
    invariant: str       # product|spending|merchant|promise|evidence|financial|execution|decision
    severity: Severity
    expected: object
    observed: object
    evidence_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class Decision:
    outcome: Literal["MATCH", "DRIFT", "HOLD"]
    findings: tuple[Finding, ...]
    receipt_hash: str       # binds the validation to one receipt version
    evaluated_at: datetime
    rules_version: str

RULES = (rules.receipt_current, rules.auth_window, rules.product_identity, rules.variant,
         rules.condition, rules.merchant, rules.amount, rules.substitution,
         rules.carrier_acceptance, rules.delivery_eta, rules.unverified_claims)

def evaluate(receipt: ReceiptTerms, auth: AuthSnapshot, evidence: Sequence[Evidence], now: datetime) -> Decision:
    findings = tuple(f for rule in RULES for f in rule(receipt, auth, evidence, now))
    sev = {f.severity for f in findings}
    outcome = "DRIFT" if "DRIFT" in sev else "HOLD" if "HOLD" in sev else "MATCH"
    return Decision(outcome, findings, receipt.content_hash, now, RULES_VERSION)
```

**Decision table (what each rule emits):**

| Rule | Condition | Severity | Code → deterministic remedy |
|---|---|---|---|
| receipt_current | receipt.status ≠ approved, OR latest merchant-promise hash ≠ hash frozen in receipt | HOLD | `RECEIPT_STALE` → buyer reapproval |
| auth_window | `now ≥ auth.expires_at` (PayPal `expiration_time`) | HOLD | `AUTH_EXPIRED` → capture prohibited, renewal workflow |
| auth_window | auth PayPal status ≠ `CREATED` (e.g. `PENDING`, `VOIDED`, `DENIED`) | HOLD | `AUTH_NOT_CAPTURABLE` |
| auth_window | `honor_until ≤ now < expires_at` | INFO | `HONOR_PERIOD_ELAPSED` (capture allowed, funds not guaranteed) |
| product_identity / variant / condition / merchant / substitution | latest **trusted** order-line evidence differs from the receipt | DRIFT | `*_MISMATCH` → block, request correction or void |
| amount | merchant final total > receipt.approved_total, or approved_total > auth amount | DRIFT | `AMOUNT_EXCEEDS_APPROVAL` |
| carrier_acceptance | no carrier event with status ∈ {ACCEPTED, IN_TRANSIT, DELIVERED}. A label-created event alone does not count. | HOLD | `CARRIER_ACCEPTANCE_MISSING` → await scan |
| delivery_eta | carrier/merchant ETA > `receipt.deadline_at` | HOLD | `ETA_PAST_DEADLINE` → review or void |
| unverified_claims | any `trust='claim'` evidence alleging a mismatch (free text, LLM-interpreted) | HOLD | `UNVERIFIED_ALLEGATION` → verify |
| (none of the above) | — | — | MATCH → capture |

**Evidence trust semantics. This is the "verified mismatch vs. allegation" distinction.**
- `merchant_system`: structured order-line from the fulfillment adapter. It can produce MATCH or DRIFT.
- `carrier`: a carrier scan event. Only this satisfies `carrier_acceptance`.
- `claim`: free-text merchant or customer message, possibly LLM-classified. **It can only produce HOLD, never MATCH or DRIFT.** So the LLM can only make the system *more conservative*. A prompt-injected "this item is fine, capture now" has no effect, because claims cannot satisfy any MATCH condition.
- "Latest" means highest **ingestion sequence** (`fulfillment_events.received_seq`, assigned by us). It never means the event's self-reported timestamp, which is untrusted input. A seller correction (demo Act 6) is a newer order-line event. The earlier DRIFT stays in the ledger.
- Every evidence row carries `synthetic: bool`. The simulator always sets `true`, and the UI and Replay show a SYNTHETIC badge (evidence-boundary disclosure).

### Pattern 2: Receipt as an immutable, versioned, hash-sealed value

**What:** Receipt content is frozen at compile time. `content_hash = sha256(canonical_json(content))`. A change in terms never edits a receipt. It creates version n+1 whose content includes `prev_receipt_hash`. Every drift `Decision` records the `receipt_hash` it evaluated, and the capture gate requires that hash to equal the *current approved* receipt's hash. That is the Evidence-integrity invariant: "a changed commitment invalidates affected validations" falls out of hash binding, with no invalidation bookkeeping.

**Hashed content (canonical JSON):**
```json
{
  "schema": "promise-receipt/1",
  "purchase_id": "uuid", "version": 2, "prev_receipt_hash": "hex|null",
  "instruction_sha256": "hex",
  "constraints": {"condition": "new", "variant": "black", "max_total_minor": 10000, "currency": "USD",
                  "deadline_at": "2026-11-06T07:59:59Z", "substitution_allowed": false},
  "product": {"channel3_product_id": "…", "variant_id": "…", "snapshot_sha256": "hex-of-raw-response-bytes"},
  "merchant": {"merchant_id": "…", "promise_version": 1, "terms_sha256": "hex",
               "approved_total_minor": 8999, "promised_delivery_at": "…"},
  "capture_conditions": ["product_identity","variant","condition","merchant","amount","carrier_acceptance","delivery_eta"],
  "rules_version": "drift-1"
}
```
Approval timestamps are *not* in the content. Approval is a separate ledger event `BUYER_APPROVED {receipt_hash}`. The buyer approves a specific hash: the approve endpoint requires the client to send back the `content_hash` it displayed, and returns 409 if it isn't current. That closes the "approved a different version than I saw" race.

**PayPal-side anchor (cheap, strong):** put `f"{purchase_id}:{receipt_hash}"` (101 chars) in the order's `purchase_units[].custom_id`. The schema allows 1–255 chars: "used to reconcile client transactions with PayPal transactions… not visible to the payer". The receipt hash then also lives in PayPal's records, and Replay can show it matching. LOW confidence: that `custom_id` propagates onto the authorization/capture resources in webhooks. The Payments v2 authorization and capture schemas do have a `custom_id` field. Verify in Phase 1.

### Pattern 3: Append-only, per-purchase hash-chained ledger

**What:** `decision_events` is the single audit log. Every fact that matters gets an event: instruction, extraction result + extractor (`llm:<model>` or `fallback`), Channel3 snapshot recorded, merchant promise recorded, receipt compiled/approved/stale/superseded, PayPal order/authorization, fulfillment evidence recorded (with `payload_sha256`), drift evaluated, capture/void requested and their results, webhook applied. Other tables hold the bulky artifacts. Events reference them by id **plus content hash**, so Replay can check that the artifacts also haven't changed.

```python
# ledger/events.py
GENESIS = "0" * 64

def append_event(conn, purchase_id, type_, payload, actor, now: datetime) -> str:
    # The purchase row is the aggregate lock AND holds the chain head. One lock serializes everything for a purchase.
    seq, prev = conn.execute(
        "SELECT chain_seq, chain_head FROM purchase_intents WHERE id=%s FOR UPDATE", (purchase_id,)).fetchone()
    body = {"purchase_id": str(purchase_id), "seq": seq + 1, "type": type_, "actor": actor,
            "occurred_at": iso_utc(now), "payload": payload, "prev_hash": prev}
    h = sha256_hex(canonical_json(body))
    conn.execute("INSERT INTO decision_events (purchase_id, seq, type, actor, occurred_at, payload, prev_hash, hash) "
                 "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (purchase_id, seq + 1, type_, actor, body["occurred_at"],
                 Jsonb(payload), prev, h))
    conn.execute("UPDATE purchase_intents SET chain_seq=%s, chain_head=%s WHERE id=%s", (seq + 1, h, purchase_id))
    return h
```

- **DB enforcement:** `UNIQUE (purchase_id, seq)` as a fork backstop, plus a trigger `BEFORE UPDATE OR DELETE ON decision_events FOR EACH ROW EXECUTE FUNCTION raise_exception()`. About ten lines, and demonstrable to judges.
- **Canonical JSON:** `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()`. This only works with these rules: **no floats anywhere in hashed data** (money as integer minor units, decimals as strings), timestamps as ISO-8601 UTC strings with fixed precision, and ASCII keys. Under those rules it matches RFC 8785 output. If you want the spec rather than the rules, `rfc8785` 0.1.4 on PyPI is a pure-Python JCS implementation.
- **Never hash Postgres `jsonb::text`.** jsonb re-orders keys and normalizes whitespace. Always hash app-side canonical bytes. Verification re-canonicalizes the parsed payload, which is safe because of the no-float rule.
- **Two times per event:** `occurred_at` comes from the injectable clock (simulated time in demos) and is hashed. `recorded_at` is a DB `DEFAULT now()` wall clock, so the UI can never pass off simulated time as real.
- **Honest limit (state it in the README):** the chain makes *recorded* history tamper-evident. It does not prove an external fulfillment event is true. And anyone with DB write access plus the code could rebuild a whole chain. The PayPal `custom_id` anchor and an exported Replay JSON are the practical external witnesses.

### Pattern 4: One purchase, one lock, plus compare-and-set on payment state

**What:** Every state-changing operation on a purchase (merchant promise update, evidence ingest + evaluation, capture claim, void, webhook apply, ledger append) starts with `SELECT … FROM purchase_intents WHERE id=$1 FOR UPDATE`. Payment transitions are additionally written as conditional updates, which are atomic in Postgres.

Postgres docs (READ COMMITTED, §13.2.1): a second concurrent `UPDATE` *waits* for the first to commit. It then **re-evaluates the WHERE clause against the updated row version** and skips the row if it no longer matches. So in two racing captures, exactly one gets a row back.

No advisory locks are needed: every operation targets an existing purchase row.

```python
# payments/service.py
def claim_capture(conn, purchase_id) -> CaptureClaim | None:
    row = conn.execute("""
        UPDATE paypal_transactions
           SET state = 'capturing', updated_at = now()
         WHERE purchase_id = %s AND state = 'authorized'
     RETURNING authorization_id, capture_request_id, auth_amount_minor, currency""",
        (purchase_id,)).fetchone()
    return None if row is None else CaptureClaim(*row)   # None => already claimed / not capturable
```
`capture_request_id = str(uuid5(NS_PROMISELOOP, f"capture:{authorization_id}"))` and `void_request_id` (`"void:{authorization_id}"`) are written **when the authorization is recorded**, so they are persisted long before any HTTP call. Retries read them from the row and never regenerate them.

### Pattern 5: Claim → commit → call → record (never call PayPal inside the deciding transaction)

**What:** Money calls happen *between* two short transactions:
1. **Tx A**: lock purchase → load snapshot → `drift.evaluate` → append `DRIFT_EVALUATED` + insert `drift_findings` → if MATCH, `claim_capture` → append `CAPTURE_REQUESTED {request_id, amount, receipt_hash}` → commit.
2. **HTTP**: `POST /v2/payments/authorizations/{id}/capture` with `PayPal-Request-Id`, `final_capture: true`, `amount` = receipt approved total. Use an httpx timeout of about 15s.
3. **Tx B**: lock purchase → apply the result through the transition table → append `CAPTURE_RESULT` → commit.

**Why:** If the process dies or times out after step 1, the durable `capturing` row plus the stored request id lets a reconcile pass retry *the same request*. PayPal's schema documents that reusing the same `PayPal-Request-Id` on capture returns **200 OK with the existing capture details**, not a second capture. If PayPal is still busy you get 409 `PREVIOUS_REQUEST_IN_PROGRESS`; wait and retry. Holding the DB transaction open across the HTTP call and rolling back on timeout would erase the only record that a capture may have happened.

---

## State Machines

### Promise Receipt lifecycle

```
            compile() fails (total > max, snapshot/constraint conflict)
  (none) ───────────────────────────────────────────────▶ REJECTED (terminal; event CONTRACT_REJECTED)
     │ compile() ok
     ▼
   DRAFT ──buyer POST /approve {content_hash == current}──▶ APPROVED
     │                                                        │ merchant promise v(n+1) with different terms_sha256,
     │ newer version compiled before approval                 │ while payment not yet captured
     ▼                                                        ▼
 SUPERSEDED ◀──────── version n+1 APPROVED ─────────────── STALE ──(compile v(n+1) → DRAFT → APPROVED)
```

| Transition | Trigger | Guard | Side effects |
|---|---|---|---|
| → REJECTED | `compile()` | `approved_total > max_total`, condition/variant not in snapshot, `promised_delivery_at > deadline_at` | No PayPal call is possible (no `ApprovedReceipt` exists). Acceptance case 4. |
| DRAFT → APPROVED | Buyer approval | Hash matches, `status='draft'`, newest version | `BUYER_APPROVED` event. Partial unique index `UNIQUE(purchase_id) WHERE status='approved'`. |
| APPROVED → STALE | Merchant promise update | New `terms_sha256` ≠ the one frozen in the receipt, and payment state ∉ {captured} | `RECEIPT_STALE` event. Payment stays `authorized`. The drift rule `receipt_current` returns HOLD, so capture is blocked. Acceptance case 5. |
| STALE/DRAFT → SUPERSEDED | Version n+1 approved (or n+1 drafted) | — | New receipt carries `prev_receipt_hash`. |
| v(n+1) APPROVED | Reapproval | New `approved_total ≤ authorization amount` (otherwise void and start a new order) | Capture gate now uses the v(n+1) hash. |

Decision integrity: no endpoint edits receipt content. The only writes are "compile a new version" (deterministic) and "approve hash X" (buyer).

### Payment lifecycle (mirrors money truth only)

**Deviation from the brief, with reasoning.** "held" is **not** a payment state. A held purchase still has a live `authorized` authorization that can be captured once evidence arrives. Mixing gate status into the money state makes "authorized but held" ambiguous and multiplies CAS guards. Keep two orthogonal facts. The **payment state** below is what PayPal holds. The **gate status** is the latest decision's outcome (MATCH/DRIFT/HOLD) plus findings, read from the ledger or `drift_findings`. The Control Tower shows both columns: "Authorization: AUTHORIZED, expires Nov 30" and "Gate: HOLD, CARRIER_ACCEPTANCE_MISSING".

Also, the brief's `capture_pending` is split in two, because two different things were conflated:
- `capturing`: *we* have claimed the capture and the request is in flight.
- `capture_pending`: PayPal created the capture with status `PENDING` (funds not settled).

```
created ──buyer approves (JS SDK onApprove / CHECKOUT.ORDER.APPROVED)──▶ approved
approved ──POST /v2/checkout/orders/{id}/authorize (auth status CREATED)──▶ authorized
authorized ──settlement MATCH + CAS──▶ capturing ──201/200 status COMPLETED──▶ captured   (terminal)
                                         │──status PENDING──▶ capture_pending ──PAYMENT.CAPTURE.COMPLETED──▶ captured
                                         │──422 AUTHORIZATION_EXPIRED──▶ expired          (terminal)
                                         │──422 AUTHORIZATION_VOIDED──▶ voided            (terminal)
                                         │──422 AUTHORIZATION_ALREADY_CAPTURED──▶ reconcile(GET order) ──▶ captured
                                         │──PAYMENT.CAPTURE.DECLINED / declined──▶ failed (terminal, operator review)
                                         └──timeout / 5xx / 409 IN_PROGRESS──▶ stays capturing; retry SAME request id
authorized ──operator void (reason required) + CAS──▶ voiding ──204 / 200──▶ voided
                                                        │──422 PREVIOUSLY_VOIDED──▶ voided
                                                        └──422 PREVIOUSLY_CAPTURED──▶ reconcile ──▶ captured (alert)
authorized ──PAYMENT.AUTHORIZATION.VOIDED webhook (manual void or validity reached)──▶ voided
authorized ──engine finds now ≥ expires_at at decision time──▶ expired (local; no capture call is made)
```

Transition rules, implemented as one table in `payments/state.py` plus one `apply(state, event) → new_state | NOOP | ILLEGAL` function:
- **Monotonic and idempotent.** Applying an event whose target equals the current state, with the same PayPal id, is a NOOP. This absorbs the race where the `PAYMENT.CAPTURE.COMPLETED` webhook lands before our own capture response is recorded.
- **ILLEGAL transitions are logged** as an event and never applied. Example: a capture claim from `voided`, which is acceptance case 11. The CAS `WHERE state='authorized'` makes it impossible anyway.
- Captures always send `final_capture: true`. The schema default is **false**. With true, PayPal itself refuses a second capture (`AUTHORIZATION_ALREADY_CAPTURED`: "If final_capture is set to true, additional captures are not possible"), a third independent layer of duplicate protection.
- Void is **operator-initiated** (Control Tower, reason code required), never automatic. A void is irreversible, and the demo needs DRIFT to stay correctable (Act 6). Capture is automatic on MATCH; that is the product.

Verified PayPal facts behind these transitions (Payments v2 / Orders v2 schemas):
- Authorization status enum: `CREATED, CAPTURED, DENIED, PARTIALLY_CAPTURED, VOIDED, PENDING` (PENDING reasons: `PENDING_REVIEW`, `DECLINED_BY_RISK_FRAUD_FILTERS`). It has a read-only `expiration_time`. **Use PayPal's `expiration_time` as the expiry source of truth.** Compute `honor_until = create_time + 3 days`; no honor-period field is returned.
- Capture status enum: `COMPLETED, DECLINED, PARTIALLY_REFUNDED, PENDING, REFUNDED, FAILED`.
- Capture responses: 201 (new), 200 (idempotent replay), 409 (`PREVIOUS_REQUEST_IN_PROGRESS`, `RESOURCE_CONFLICT`), 422 (`AUTHORIZATION_EXPIRED`, `AUTHORIZATION_VOIDED`, `AUTHORIZATION_DENIED`, `AUTHORIZATION_ALREADY_CAPTURED`, `MAX_CAPTURE_AMOUNT_EXCEEDED`, `DUPLICATE_INVOICE_ID`, …).
- Void: 204 No Content by default, 200 with `Prefer: return=representation`. 422 `PREVIOUSLY_CAPTURED` / `PREVIOUSLY_VOIDED`. "You cannot void an authorized payment that has been fully captured."
- Order status enum: `CREATED, SAVED, APPROVED, VOIDED, COMPLETED, PAYER_ACTION_REQUIRED`. "To successfully authorize payment for an order, the buyer must first approve the order or a valid payment_source must be provided." After creation, the payer approval window is 6 hours by default.
- Honor period 3 days; authorization valid 29 days; reauthorization issues a new authorization ID and restarts a 3-day honor period. **The sources contradict each other on reauthorization count:** the endpoint description says "multiple re-authorizations", the request schema says "only once". This is P1 only, so it doesn't block. Reauthorize is described for "PayPal account payments".

---

## Idempotency: five independent layers

| Layer | Mechanism | Protects against |
|---|---|---|
| 1. Inbound fulfillment dedup | `UNIQUE (source, external_event_id)` on `fulfillment_events`; `INSERT … ON CONFLICT DO NOTHING RETURNING id`; duplicate → return 200, no re-evaluation | Same carrier/merchant event delivered twice |
| 2. Inbound webhook dedup | Partial unique index `UNIQUE (paypal_event_id) WHERE verification='verified'`; dedup row inserted in the **same tx** as the state transition | PayPal retries (up to 25 times over 3 days); manual resend via `POST /v1/notifications/webhooks-events/{id}/resend` |
| 3. Purchase lock + CAS | `FOR UPDATE` on purchase, `UPDATE … WHERE state='authorized'` | Two events racing to capture in our process |
| 4. PayPal-Request-Id | Deterministic `uuid5("capture:{auth_id}")` / `uuid5("void:{auth_id}")`, persisted before the call. A UUID fits PayPal's 38-char limit. Must be "unique for both each request and an API call type". | Our own retries after timeout or crash |
| 5. PayPal business rule | `final_capture: true` → `AUTHORIZATION_ALREADY_CAPTURED` | Everything above failing |

PayPal's idempotency page: omitting the header means "PayPal duplicates the request". Simultaneous requests with the same id: "PayPal processes the first request and might fail the second". Retention is "for a period of time", API-specific, with no number published. That's why layer 5 and the reconcile-by-GET path exist. A retry days later must not depend on PayPal still remembering the key.

**`invoice_id` pitfall:** invoice ids must be unique per merchant account. Use the purchase UUID, never a human-friendly `PL-00001` counter. A dev DB reset restarts the counter, and the Sandbox then returns `DUPLICATE_INVOICE_ID` on every rerun.

---

## Webhook Processing

**Verification: self-verification, no postback.** PayPal's webhook docs call self cryptographic verification "the preferred method" because it needs no extra API call. The postback API (`POST /v1/notifications/verify-webhook-signature`) is "not usable for mock test webhooks", and it requires posting the event back "exactly as it was received". Self-verification also makes acceptance case 10 an **offline unit test** with a self-signed cert.

```python
# webhooks/verify.py (pure; cert_loader injected, cached by URL)
def verify(headers: Mapping[str, str], raw_body: bytes, webhook_id: str, cert_loader) -> bool:
    try:
        url = urlparse(headers["paypal-cert-url"])
        if url.scheme != "https" or not (url.hostname or "").endswith(".paypal.com"):
            return False                       # SSRF + forged-cert guard (not in PayPal's sample code)
        msg = (f'{headers["paypal-transmission-id"]}|{headers["paypal-transmission-time"]}|'
               f'{webhook_id}|{zlib.crc32(raw_body)}').encode()   # CRC32 of RAW bytes, decimal
        cert_loader(headers["paypal-cert-url"]).public_key().verify(
            base64.b64decode(headers["paypal-transmission-sig"]), msg, padding.PKCS1v15(), hashes.SHA256())
        return True
    except (KeyError, ValueError, InvalidSignature):
        return False
```

- Read `await request.body()` **before** any JSON parsing. PayPal: "You must use the original raw body to calculate this."
- `webhook_id` comes from config (`PAYPAL_WEBHOOK_ID`, the id returned when you subscribed the Render URL). PayPal mock/simulator events use the literal webhook id `WEBHOOK_ID`. Accept that only when `ACCEPT_SIMULATOR_WEBHOOKS=true` (sandbox).
- The cert-URL host allowlist is our addition; PayPal's sample fetches any URL. LOW confidence on the exact host (`api.sandbox.paypal.com` / `api.paypal.com` observed in practice). Log the real header from the first Sandbox delivery and tighten the check.

**Processing: synchronous, in-request, one transaction. No BackgroundTasks, no worker, no Render Workflows.**

```
POST /webhooks/paypal
  raw = body; ok = verify(...)
  if not ok: INSERT webhook_events(verification='rejected', …) ; return 400      # never touches dedup index
  BEGIN
    INSERT webhook_events(verification='verified', paypal_event_id, …) ON CONFLICT DO NOTHING RETURNING id
      → no row: COMMIT; return 200 (duplicate)
    find purchase by resource.custom_id → else by authorization_id/capture_id
      → none: mark 'unmatched'; COMMIT; return 200  (reconcile() re-applies later)
    lock purchase; payments.apply(state, event); append_event(WEBHOOK_APPLIED, {event_id, type, resource_id})
  COMMIT; return 200
  (exception → rollback → 500 → PayPal retries: PayPal's retry IS the queue)
```

Why synchronous is correct here:
- The work is milliseconds (cert cached, a few row writes). PayPal retries any non-2xx, timeout or connection failure "up to 25 times over 3 days", which is a durable retry mechanism for free.
- FastAPI `BackgroundTasks` run "after returning a response" in the same process. Render "might restart a Free web service at any time", so a task queued there is lost. Use BackgroundTasks only for non-money work, such as generating the LLM explanation text for Replay.
- Render Free instances support web services, Postgres and Key Value only. Background workers and cron jobs are not free. Render Workflows bill compute per task run, define tasks via a separate Python/TS SDK, and "task runs can't receive incoming network connections". That's a second deploy unit for sub-second work. **Skip it** (the product doc made it conditional on being straightforward; it isn't worth it).

Event types to subscribe and handle (PayPal event-names page): `CHECKOUT.ORDER.APPROVED`, `CHECKOUT.PAYMENT-APPROVAL.REVERSED`, `PAYMENT.AUTHORIZATION.CREATED`, `PAYMENT.AUTHORIZATION.VOIDED` (manual void **or** "authorization reaching its 30 day validity period"; there is no separate "expired" event), `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.PENDING`, `PAYMENT.CAPTURE.DECLINED` (v2 has no `PAYMENT.CAPTURE.DENIED`), and `PAYMENT.CAPTURE.REFUNDED` / `REVERSED` (record only; P1). Anything else: store, 200, no-op.

**Source-of-truth rule:** our synchronous API responses (authorize, capture, void) are primary. Webhooks *confirm* and catch asynchronous changes (PENDING→COMPLETED, validity-period voids, approval reversals). `settlement.reconcile(purchase_id)` resolves any doubt with `GET /v2/checkout/orders/{id}` (`purchase_units[].payments` has `authorizations`, `captures`, `refunds`). It runs on demand from the Control Tower and once at startup for rows stuck in `capturing`/`voiding`, and it re-applies `unmatched` webhooks.

---

## Injectable Clock

```python
class Clock(Protocol):
    def now(self) -> datetime: ...          # always tz-aware UTC

class SystemClock:     now = lambda self: datetime.now(UTC)
class FixedClock:      ...                   # tests: settable, advance(timedelta)
class DemoOffsetClock: ...                   # SystemClock + offset; enabled only when DEMO_MODE=true
```

- `drift.evaluate` never sees a clock, only `now`. `settlement` reads `clock.now()` **once per decision** and passes it everywhere: engine, ledger `occurred_at`, latency metric.
- FastAPI: `def get_clock() -> Clock`; tests use `app.dependency_overrides[get_clock] = lambda: fixed`.
- Expiry is evaluated **lazily at decision time**, with no scheduler. The Control Tower's "expiring soon" filter computes `expires_at - now` in its query using the same clock. A Control Tower button can "advance demo clock +30 days" to show acceptance case 8 live, labeled as simulated time.
- Safety property: the demo clock can only make the system *more* conservative. Moving time forward makes us refuse captures PayPal would allow. It can never make PayPal accept an expired authorization; PayPal would return 422 `AUTHORIZATION_EXPIRED`, which maps to `expired`.
- Deadlines: "by Nov 5" is a date in the buyer's timezone. Store `deadline_at` as the UTC instant of end-of-day in the buyer's tz, and compare instants only.

---

## Data Flow

### Flow 1: Instruction → approved contract → authorization (Acts 1–4)

```
Shopper text ──▶ api/shopper ──▶ intent.extract (LLM, timeout+schema; fallback on failure)
                                   └─▶ draft IntentConstraints (+extractor tag) ──▶ ledger INSTRUCTION_RECEIVED
Buyer edits/confirms constraints ──▶ catalog.search (Channel3) ──▶ product_snapshots(raw bytes, sha256)
Buyer picks product+variant ──▶ merchant quote (separate source; simulator in MVP) ──▶ merchant_promises v1
receipts.compile(constraints, snapshot, promise) ──▶ REJECTED (over limit) | DRAFT(content, hash)
Buyer approves hash ──▶ APPROVED ──▶ payments.create_order(ApprovedReceipt)
   POST /v2/checkout/orders {intent: AUTHORIZE, custom_id: purchase:hash, invoice_id: purchase uuid}
Buyer approves at PayPal (JS SDK) ──▶ POST /v2/checkout/orders/{id}/authorize ──▶ authorized
   (store authorization_id, amount, create_time, expiration_time; honor_until = create_time+3d)
```

### Flow 2: Evidence → decision → conditional settlement (Acts 5–7)

```
Fulfillment event (simulator / adapter) ──▶ api/fulfillment ──▶ settlement.ingest_and_evaluate
  Tx A: lock purchase → dedup insert → ledger EVIDENCE_RECORDED
        → drift.evaluate(receipt, auth, evidence, now) → ledger DRIFT_EVALUATED + drift_findings
        → MATCH? claim_capture (CAS) → ledger CAPTURE_REQUESTED
  HTTP: POST /v2/payments/authorizations/{id}/capture (PayPal-Request-Id, final_capture=true)
  Tx B: lock → payments.apply(result) → ledger CAPTURE_RESULT
Later: PAYMENT.CAPTURE.COMPLETED webhook ──▶ verify → dedup → apply (NOOP if already captured) → ledger
```

### Flow 3: Promise Replay assembly (Act 8)

Computed on read. No projection table; a purchase has tens of events.

```
replay(purchase_id):
  events = SELECT * FROM decision_events WHERE purchase_id=$1 ORDER BY seq
  chain  = verify_chain(events)        # recompute each hash; report first broken seq, if any
  artifacts = check referenced rows: snapshot sha256(raw) == recorded; receipt hash == recompute(content);
              fulfillment payload_sha256 == recorded
  steps  = group events by STEP_OF[event.type] into the 10 doc steps:
     1 INSTRUCTION_RECEIVED  2 PRODUCTS_DISCOVERED  3 PRODUCT_SELECTED  4 MERCHANT_PROMISE_RECORDED
     5 RECEIPT_APPROVED      6 PAYPAL_ORDER_CREATED/AUTHORIZED          7 EVIDENCE_RECORDED
     8 DRIFT_EVALUATED       9 REMEDY (deterministic code→remedy; optional LLM prose, labeled)
    10 CAPTURE/VOID RESULT + WEBHOOK_APPLIED
  divergence = first DRIFT_EVALUATED with outcome != MATCH (highlight its findings expected vs observed)
  return {chain_valid, broken_at, artifacts_valid, steps, divergence, receipt_versions, paypal_anchor}
```

Expose it as `GET /purchases/{id}/replay` (JSON, also downloadable for judges). The Replay view only renders it. The `STEP_OF` dict is the single mapping, which keeps the UI dumb and the test simple: a golden-file test on the demo scenario's replay JSON.

---

## Testing Architecture

| Layer | Scope | Infra | Runs in verify.sh |
|---|---|---|---|
| L0 pure | drift rules + `evaluate` table; receipt `compile` validation; canonical-hash golden vectors; payment transition table (every from×event pair); webhook `verify` with a self-signed RSA cert from `cryptography` | none | yes (seconds) |
| L1 service | settlement idempotency and **concurrency race** (2 threads, 2 connections, same evidence → `FakeGateway.capture_calls == 1`); stale→reapprove flow; webhook dedup; chain tamper detection (edit a payload with the trigger disabled → `verify_chain` reports the seq) | Postgres via Docker, `FakeGateway`, `FixedClock` | yes |
| L2 gateway contract | One test module parametrized over `FakeGateway` and `PayPalGateway`: idempotent capture replay (200 + same id), capture after void → `AUTHORIZATION_VOIDED`, void after capture → `PREVIOUSLY_CAPTURED`, second capture → `AUTHORIZATION_ALREADY_CAPTURED`. **This keeps the fake honest.** | Sandbox (`-m sandbox`, manual) | no (needs creds + approved order) |
| L3 e2e | 8-act demo script against the Render URL | Render + Sandbox | manual, before recording |

**Acceptance-case placement:**

| # | Case | Where it is proven |
|---|---|---|
| 1 | Exact match → capture | L0 engine (MATCH) + L1 settlement (Fake capture called once) + L3 demo |
| 2 | Wrong variant → blocked | L0 engine `VARIANT_MISMATCH` DRIFT |
| 3 | Refurbished → blocked | L0 engine `CONDITION_MISMATCH` DRIFT |
| 4 | Total > limit → rejected before auth | L0 `compile()` REJECTED; L1: no `create_order` call |
| 5 | Merchant changes terms → stale | L1 receipt service + L0 `receipt_current` HOLD |
| 6 | Carrier event missing → hold | L0 `CARRIER_ACCEPTANCE_MISSING` (label-only fixture included) |
| 7 | ETA past deadline → hold | L0 `ETA_PAST_DEADLINE` (with timezone edge fixture) |
| 8 | Auth expired → prohibited | L0 `AUTH_EXPIRED` via `now`; L1: no capture call; Fake returns 422 if forced |
| 9 | Duplicate event → one capture | L1 sequential **and** concurrent duplicates |
| 10 | Bad webhook signature → rejected | L0 `verify` false (tampered body, wrong sig, non-PayPal cert host, missing header); L1: no dedup row created |
| 11 | Already voided → no capture | L0 transition ILLEGAL; L1 CAS returns None; Fake capture calls == 0 |

**Labeled dataset (15–20 scenarios):** `tests/scenarios/*.json`, each `{id, label, receipt, auth, evidence[], now, expected_outcome, expected_codes[]}`. It has three consumers:
1. `pytest` parametrize (correctness).
2. `scripts/metrics.py`: detection rate, unsafe-capture prevention, false-block rate (valid scenarios not MATCH), decision latency (p50/p95 of `evaluate` + settle against Fake), duplicate prevention (replayed-event scenarios), expiry handling. It prints the README table.
3. Optionally, a demo seeder that loads them into the Control Tower grid, so it isn't empty.

Mix: about 5 valid, 3 variant/condition, 2 price, 2 substitution/merchant, 2 late ETA, 2 missing carrier, 2 replayed events, 2 expiry (one in honor period, one past expiry), 1 unverified claim.

**Sandbox approval for L2 (LOW confidence, Phase 1 spike):** authorizing needs buyer approval or a valid `payment_source`. Plan for a scripted half-manual flow: the script creates the order and prints the approve URL, you approve with the Sandbox buyer, then it runs capture/void assertions. A card `payment_source` may allow full automation but depends on account eligibility; don't plan on it. `PayPal-Mock-Response` (`{"mock_application_codes": "..."}`) is documented for capture, void, authorize and show-authorization. Only `DUPLICATE_INVOICE_ID` is confirmed as an example code. Test which 422 codes it can force before relying on it.

---

## Suggested Build Order (aligned to the doc's checkpoints)

Dependencies: `core` → `payments` + `webhooks` (money spine) → `ledger` → `receipts` (+`intent`, `catalog`) → `drift` → `settlement` → `replay`/`tower`. The pure `drift` engine has no dependencies, so fill credential-waiting time with it.

| Window | Build | Exit proof | Why this order |
|---|---|---|---|
| **Oct 31–Nov 2** (hard gate) | `core` (config, clock, canon, db, `schema.sql`); `payments` (OAuth token cache, create order AUTHORIZE, authorize, capture, void, GET; `FakeGateway`; transition table; request ids); minimal approve page (JS SDK); **deploy to Render on day 1**; register webhook URL; `webhooks.verify` + processor; one Channel3 curl to confirm the key | Sandbox: authorize→capture and authorize→void succeed; a verified webhook lands in `webhook_events` on Render; duplicate capture call returns 200 with same capture id | Highest external risk; the webhook needs a public URL; everything else depends on a real auth id. If not green by Nov 2, cut scope. |
| **Nov 3–4** | `ledger` (append, chain, trigger); `intent` (LLM + fallback); `catalog` (raw snapshot); merchant promise (simulator); `receipts` compiler + lifecycle; Shopper Agent view; `create_order` takes `ApprovedReceipt`, sets `custom_id` | Buyer approves an exact contract hash → real Sandbox authorization bound to it; over-limit is rejected before any PayPal call | Receipt is the input type for both the engine and the gate. The ledger must exist before the first business event. |
| **Nov 5–6** | `fulfillment` (ingest, dedup, trust, simulator); `drift` rules + `evaluate`; L0 acceptance table; scenario dataset v1 | Wrong variant and refurbished deterministically DRIFT; missing carrier → HOLD; tests green | Pure code, cheapest to perfect; the dataset is reused for metrics. |
| **Nov 7–8** | `settlement` (Tx A / HTTP / Tx B, claim CAS, void, reconcile); expiry via clock; webhook transitions for capture completed/pending; L1 concurrency tests; Replay API + view | Demo Acts 5–8 on Sandbox: blocked → corrected → real capture → webhook → Replay with valid chain; 2 racing events → 1 capture | Needs receipts, engine and money spine all present. |
| **Nov 9–10** | Control Tower (AG Grid exception grid first, AG Studio only if time allows); `metrics.py`; security pass (import-linter contracts, secrets, cert-host allowlist); clean-session run on Render; Postman collection | Full workflow from a fresh browser session on the public URL | UI over existing endpoints; no new backend logic. |
| Nov 11–12 | README, video, submission | — | — |

**Research flags for phases:**
- Phase 1 needs a spike: Sandbox buyer approval UX (JS SDK vs approve link), the real `paypal-cert-url` host, whether `custom_id` appears on authorization/capture webhook resources, and which `PayPal-Mock-Response` codes work on capture/void.
- Phase 3 (drift) and Phase 4 (settlement) follow standard patterns. Use this document; no further research needed.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|---|---|
| Hackathon / demo (≤100 purchases) | As designed: one web service, synchronous everything, replay computed on read. |
| ~10k purchases/day | Move the PayPal capture call out of the request into a DB outbox (`capturing` rows are already the outbox) drained by one worker. Add an index on `paypal_transactions(state, expires_at)` for the tower. |
| Beyond | Partition `decision_events` by time; per-merchant webhook ingestion. Not relevant for this project. |

### Scaling Priorities
1. **First bottleneck:** inline PayPal latency on the evidence request (about 1–2s). The fix is already shaped: the claim/commit/call split means a worker can take over step 2 unchanged.
2. **Second bottleneck:** Render Free spin-down. After 15 idle minutes the first request (including a webhook) waits about 1 minute for spin-up. Use a paid instance for the judging window, or accept that PayPal's retries deliver late.

---

## Anti-Patterns

### Anti-Pattern 1: Giving the LLM tools, or letting its output flow to payments
**What people do:** Function-calling "capture_payment"; using extracted constraints directly as the contract.
**Why it's wrong:** Product descriptions and merchant messages are untrusted text. Injection becomes a money-movement path.
**Do this instead:** The LLM has no tools. Its output is a draft that must pass `compile()` and a buyer hash approval. `claim` evidence can only HOLD. import-linter forbids the import path transitively.

### Anti-Pattern 2: A random `uuid4()` PayPal-Request-Id per attempt
**What people do:** Generate the idempotency key inside the HTTP client call.
**Why it's wrong:** A retry after a timeout gets a new key, and PayPal treats it as a new request: a double capture, absent `final_capture`.
**Do this instead:** Derive the key deterministically from `(action, authorization_id)`, persist it in the claim transaction, and read it back on retry.

### Anti-Pattern 3: Calling PayPal inside the transaction that decides
**What people do:** `BEGIN; evaluate; capture(); UPDATE; COMMIT`. On timeout, roll back.
**Why it's wrong:** PayPal may have captured. The rollback erases your evidence of the attempt, and the next trigger captures again or leaves money untracked.
**Do this instead:** Pattern 5 (claim → commit → call → record), with `reconcile()` by GET.

### Anti-Pattern 4: Dedup row written before signature verification
**What people do:** `INSERT webhook_events(event_id)` first, then verify.
**Why it's wrong:** An attacker who sends a forged body carrying a real future event id poisons the dedup index, and the genuine PayPal delivery is dropped as a "duplicate".
**Do this instead:** Verify first. Rejected attempts are logged with `verification='rejected'`, outside the partial unique index.

### Anti-Pattern 5: "held" stored as a payment state / a scheduler for expiry
**What people do:** Add `held` to the payment enum; add a cron job to flip auths to expired.
**Why it's wrong:** Gate status and money status diverge and need syncing. Cron isn't on Render Free, and it is another moving part.
**Do this instead:** Payment state mirrors PayPal. Gate status comes from the latest decision. Expiry is evaluated lazily from `expires_at` and the injected `now`.

### Anti-Pattern 6: Floats and DB-serialized JSON in hashes
**What people do:** `sha256(json.dumps(row))` with float prices, or hashing `jsonb::text`.
**Why it's wrong:** Float formatting and jsonb normalization change bytes, so verification fails on untampered data and the "tamper-evident" claim collapses during the demo.
**Do this instead:** Integer minor units, ISO-UTC strings, app-side canonical JSON, golden-vector tests.

### Anti-Pattern 7: Trusting event-supplied timestamps for "latest evidence"
**What people do:** Order fulfillment events by `payload.timestamp`.
**Why it's wrong:** A merchant can backdate or forward-date a record to choose which one wins.
**Do this instead:** Order by our ingestion sequence. Keep their timestamp as observed data only.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---|---|---|
| PayPal REST (Sandbox `https://api-m.sandbox.paypal.com`) | `PaymentGateway` protocol; httpx client with OAuth2 client-credentials token cached until expiry; explicit timeouts; every POST with a `PayPal-Request-Id` | Use `expiration_time` for expiry; `final_capture: true`; `custom_id` = purchase:receipt hash; `invoice_id` = purchase UUID; amounts as strings from Decimal |
| PayPal Webhooks | Self-verified, sync processing, dedup by event id | Subscribe the Render URL on day 1; mock events use webhook id `WEBHOOK_ID` |
| Channel3 | `catalog` adapter returns raw bytes + parsed; sha256 of raw stored | Not trusted for checkout total (merchant quote is separate) |
| Gemini / OpenRouter | One OpenAI-compatible client in `intent`; strict schema validation; timeout + backoff; deterministic fallback for the demo instruction | No credentials or tools passed to the model |
| Render | Static site (frontend) + web service (FastAPI) + Postgres | Free Postgres **expires 30 days after creation**: created ~Nov 1, it expires ~Dec 1, possibly inside the judging window. Free web service sleeps after 15 min. |

### Internal Boundaries

| Boundary | Communication | Notes |
|---|---|---|
| api → settlement / receipts / intent / catalog | Direct function calls, one tx per request | Routers stay thin; no business logic |
| settlement → drift | Pure call with loaded snapshot values | Under the purchase lock |
| settlement → payments | `claim_*` (SQL CAS) + gateway call + `apply` | The only capture/void path |
| webhooks → payments | `apply(state, event)` | Same transition table as settlement uses |
| all services → ledger | `append_event(conn, …)` inside the caller's tx | The event commits atomically with the state change |
| intent / catalog / drift → payments, settlement, webhooks | **Forbidden** (import-linter, transitive) | Build fails on violation |

---

## Sources

PayPal (primary, HIGH):
- [Payments v2 API reference](https://developer.paypal.com/docs/api/payments/v2/), plus its OpenAPI schema `https://developer.paypal.com/api/payments/v2/schema.json`: capture/void/reauthorize parameters and responses, `final_capture` default false, status enums, `expiration_time`, error names, idempotent 200 replay example
- Orders v2 OpenAPI schema `https://developer.paypal.com/api/orders/v2/schema.json`: `AUTHORIZE` intent, `/authorize` precondition, order status enum, 6-hour approval window, `custom_id` / `invoice_id` limits, `payment_collection`
- [Authorize a payment and capture later](https://developer.paypal.com/docs/checkout/standard/customize/authorization/): 3-day honor period, 29-day validity, reauthorization behavior
- [Idempotency](https://developer.paypal.com/api/rest/reference/idempotency/): PayPal-Request-Id semantics, retention unspecified, simultaneous-request behavior
- [Webhooks integration](https://developer.paypal.com/api/rest/webhooks/rest/): self-verification preferred, signed-message format, CRC32 of raw body, 25 retries over 3 days, mock-event behavior
- Webhooks v1 OpenAPI schema `https://developer.paypal.com/api/webhooks/v1/schema.json`: verify-webhook-signature fields, resend endpoint
- [Webhook event names](https://developer.paypal.com/api/rest/webhooks/event-names/): authorization/capture/order events; VOIDED covers the validity period; v2 uses DECLINED
- [Negative testing request headers](https://developer.paypal.com/tools/sandbox/negative-testing/request-headers/): `PayPal-Mock-Response` support list

Platform (HIGH):
- [PostgreSQL: Transaction Isolation §13.2.1](https://www.postgresql.org/docs/current/transaction-iso.html): READ COMMITTED UPDATE wait and WHERE re-evaluation
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/): run after response, same process
- [Render Free instances](https://render.com/docs/free): service types, 15-min spin-down, 30-day Postgres expiry, restarts
- [Render Workflows](https://render.com/docs/workflows): SDK-defined tasks, per-run billing, no inbound connections
- [import-linter Forbidden contracts](https://import-linter.readthedocs.io/en/stable/contract_types/forbidden/): transitive checking, external packages
- PyPI: `rfc8785` 0.1.4 (RFC 8785 JCS), `import-linter` 2.15 (checked 2026-10-31)

---
*Architecture research for: promise-gated PayPal settlement (agentic commerce)*
*Researched: 2026-10-31*
