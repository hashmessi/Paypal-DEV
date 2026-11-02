# Phase 02: Promise Receipt — Context & Requirements Lock

**Phase:** 02-promise-receipt  
**Goal:** A buyer turns a natural-language instruction into an exact, hash-sealed Promise Receipt they approve, and the real Sandbox authorization is bound to that receipt hash.  
**Depends On:** Phase 01 (Money Spine on a Public URL)  

---

## 1. Requirements Lock

### Intent Extraction (INTENT-01, INTENT-02, INTENT-03)
- Natural-language instruction -> typed constraints schema:
  - `product_type`: str (e.g. "over-ear headphones")
  - `condition`: "new" | "refurbished" | "any"
  - `color`: Optional[str] (e.g. "black")
  - `max_total_cents`: int (minor cents, e.g. 10000 for $100.00)
  - `currency`: str (default "USD")
  - `deliver_within_days`: int (relative days, e.g. 5)
  - `substitutions_allowed`: bool (default False)
- Multi-tier provider chain:
  1. Primary: Google Gemini (`gemini-2.0-flash` or `gemini-1.5-flash` with structured outputs / Pydantic schema)
  2. Secondary: OpenRouter free models (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-exp:free`)
  3. Deterministic Fallback: Rule-based regex extractor that reliably parses product, price (`under $X`), condition, color, and delivery time (`within X days`) with zero external API calls.
- Extraction Cache: SHA-256 of lowercase, whitespace-trimmed instruction -> cached constraints.
- Clock Resolution (INTENT-02): Deadlines resolved in code via `clock.today() + timedelta(days=deliver_within_days)`. No LLM hallucinated calendar dates.
- Source Tagging (INTENT-03): Constraints tagged with `source: "ai" | "fallback"`.

### Discovery & Merchant Quote (DISC-01, DISC-02, DISC-03)
- Channel3 Product Search Adapter:
  - Real Channel3 API client when `CHANNEL3_API_KEY` is provided.
  - Comprehensive synthetic catalog fallback: Sony WH-1000XM5 headphones with multiple offers (Brand New in Black, Brand New in Silver, Certified Refurbished, and unverified condition offers).
- Snapshot Rules (DISC-02):
  - Store raw Channel3 response bytes/string directly in `product_snapshot`.
  - Null condition handling: if `condition is None`, it is strictly marked `UNVERIFIED`, never promoted to `NEW`.
  - Non-USD offers are rejected with `CurrencyNotSupportedError`.
- Merchant Quote (DISC-03):
  - Subtotal, shipping, tax, total (all integer minor cents).
  - Merchant name and domain.
  - Label: `"Sandbox stand-in for <domain>"`.

### Receipt Compilation & Immutability (RCPT-01, RCPT-02, RCPT-03, RCPT-04)
- RFC 8785 Canonical JSON scheme:
  - Lexicographical key sorting.
  - No whitespace separators.
  - Strict integer minor units for monetary amounts (floats strictly rejected).
- SHA-256 Digest: `receipt_hash = sha256_hex(canonical_json(receipt_payload))`.
- Budget Enforcement (RCPT-02):
  - If `quote.total_cents > constraints.max_total_cents`, raise `BudgetExceededError`.
- Approval Gate (RCPT-03):
  - Buyer approves specific `receipt_hash`.
  - If incoming approval hash does not match current receipt version hash, raise HTTP 409 Conflict (`STALE_RECEIPT_HASH`).
- Versioning & Stale Transitions (RCPT-04):
  - If merchant modifies terms (price change, ETA shift), compiler creates new receipt version (`version = current_version + 1`), marks previous version `stale`, and requires reapproval.
  - Database layer: Approved receipts are immutable. Any attempt to modify an approved receipt raises an error.

### Gateway Binding (PAY-08)
- When PayPal Order is created for an approved receipt, `purchase_units[0].custom_id` carries `receipt_hash`.
- Ensures PayPal authorization hold is cryptographically bound to the receipt.

### Frontend Integration (UI-01)
- Interactive Shopper Agent view (`/shop` or `/`):
  - Buyer types instruction.
  - Sees extracted constraints with `AI` or `Fallback` badge, allows in-place editing.
  - Selects product candidate & views merchant quote.
  - Approves receipt hash.
  - Renders PayPal Authorize Button with receipt hash in payload.

