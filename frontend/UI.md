# PromiseLoop — Frontend UI

Final frontend design and build guide for **PromiseLoop: promise-gated payments for agentic commerce**.
Premium, minimal, enterprise-fintech. Light theme only.

| | |
|---|---|
| **Status** | Design contract complete. **Not yet implemented**: `frontend/src` is still the Vite template scaffold. |
| **Contract (tokens, vocabulary, copy, don'ts)** | `.planning/ui/UI-SPEC.md` — wins on any conflict with this file |
| **Research (hypotheses, test plan)** | `.planning/ui/USER-RESEARCH.md` |
| **Visual reference** | The three approved mocks: Control tower · Promise drift review · Promise Receipt |
| **Stack (locked)** | React 19 · Vite 8 · TypeScript 7 · Tailwind 4 · React Router 8 (data mode) · TanStack Query 5 · AG Grid Community 36.2 · `@paypal/react-paypal-js` |

---

## 1. Principles

1. **Money state and gate state are different facts.** Always show *Authorization* and *Gate* separately. "Authorized" is amber, never green, never "paid".
2. **Show the reason, not just the verdict.** Every block shows expected vs observed, the invariant code and what unblocks it.
3. **Deterministic code decides; the UI says so.** AI text is labeled and sits under the finding. There is no capture button; capture is an outcome.
4. **Be honest about what is simulated.** `SYNTHETIC`, `UNVERIFIED`, "Sandbox stand-in for `<domain>`", "Not an escrow service".
5. **Quiet interface.** White surfaces, gray hairlines, one blue accent. Hierarchy comes from type and spacing, not color or shadow.
6. **A judge with no keys finishes the demo in five minutes.** Everything else yields to that.

---

## 2. Design tokens

Implement once in `src/index.css`. Replace the template CSS entirely (delete `App.css` and the `index.css` template rules).

```css
@import "tailwindcss";
@import "@fontsource-variable/inter";
@import "@fontsource-variable/jetbrains-mono";

@theme {
  --font-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono Variable", ui-monospace, monospace;

  /* surfaces */
  --color-surface: #ffffff;
  --color-canvas: #f6f7fb;
  --color-inset: #f8fafc;
  --color-line: #e5e7eb;
  --color-line-strong: #d1d5db;

  /* text */
  --color-ink: #0f172a;
  --color-muted: #596579;

  /* accent (reserved list in UI-SPEC) */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-soft: #eff6ff;

  /* status tones: text / tint / border */
  --color-ok: #15803d;      --color-ok-soft: #ecfdf3;      --color-ok-line: #bbf7d0;
  --color-warn: #b45309;    --color-warn-soft: #fff7e6;    --color-warn-line: #fde7b0;
  --color-bad: #b91c1c;     --color-bad-soft: #fef2f2;     --color-bad-line: #fecaca;
  --color-neutral: #475569; --color-neutral-soft: #f1f5f9; --color-neutral-line: #e2e8f0;

  /* status tone: info (in-flight only) */
  --color-info: #1d4ed8; --color-info-soft: #eff6ff; --color-info-line: #bfdbfe;

  /* type scale: 12 / 14 / 18 / 28 only. Reset Tailwind defaults so text-lg / font-medium cannot bypass the contract */
  --text-*: initial;
  --font-weight-*: initial;
  --font-weight-normal: 400;
  --font-weight-semibold: 600;
  --text-label: 0.75rem;   --text-label--line-height: 1.33;
  --text-body: 0.875rem;   --text-body--line-height: 1.5;
  --text-heading: 1.125rem; --text-heading--line-height: 1.33;
  --text-display: 1.75rem; --text-display--line-height: 1.2;

  --radius-control: 8px;
  --radius-card: 12px;
  --shadow-card: 0 1px 2px rgb(15 23 42 / 0.04);
}

html { color-scheme: light; background: var(--color-canvas); }
body { font-family: var(--font-sans); font-size: 14px; color: var(--color-ink); font-feature-settings: "cv11", "ss01"; }
:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
.num { font-variant-numeric: tabular-nums; }
@media (prefers-reduced-motion: reduce) { * { transition-duration: 0ms !important; animation: none !important; } }
```

Install: `npm i @fontsource-variable/inter @fontsource-variable/jetbrains-mono lucide-react` (verify each with `npm view` first; commit the lockfile).
Set `<html lang="en">`, `<title>PromiseLoop</title>`, and replace `favicon.svg` with the logo mark (blue rounded square, white "P").

Rules: spacing from the 4 px scale (`xs 4 · sm 8 · md 16 · lg 24 · xl 32 · 2xl 48 · 3xl 64`); radius 8 controls / 12 cards / pill badges; weights 400 and 600 only; shadow only `--shadow-card`.

---

## 3. App shell

```
┌────────────┬──────────────────────────────────────────────────────────────┐
│ ▣ PromiseLoop      │ Demo Merchant A / Control tower         [SANDBOX ENVIRONMENT] [clock] (DM) │ 64
│ 232 px     ├──────────────────────────────────────────────────────────────┤
│ WORKSPACE  │  page gutter 32                                               │
│ ▢ Control tower                                                              │
│ ▢ Promise receipts   canvas #F6F7FB                                          │
│ ▢ Drift queue  (3)                                                           │
│ ▢ Event history                                                              │
│ DEMO                                                                          │
│ ▢ Shopper agent                                                              │
│ ▢ Proof                                                                      │
│ ─────────── │                                                                │
│ DEMO MERCHANT│                                                               │
│ (DM) Demo Merchant A · Sandbox                                               │
└────────────┴──────────────────────────────────────────────────────────────┘
```

- **Sidebar** (white, right hairline): logo (24 px accent rounded square + "PromiseLoop" Heading), nav items 40 px tall, active = `accent-soft` fill + accent text + 600; count badge on Drift queue (`bad-soft`/`bad`, `aria-label="3 open cases"`). Footer card: avatar initials, merchant name, "Merchant workspace".
- **Topbar** (white, bottom hairline, 64 px): breadcrumb (`Demo Merchant A / Page`, current in ink 600), right side: `SANDBOX ENVIRONMENT` neutral pill (Label, uppercase), **demo-clock chip** (hidden at offset 0; otherwise warning "Simulated time +30d"), avatar.
- **Main**: `max-w-[1280px]`, padding 32; page header = eyebrow (Label uppercase muted) → `h1` Display → one-line description (muted) with actions right-aligned and top-aligned to the `h1`.
- **Banners** (below topbar, full width, 1 px tint): cold start, simulated clock, API unreachable.
- No accounts. The merchant is the fixed demo merchant; do not build login, workspace switching or avatar menus.

Responsive: see §11.

---

## 4. Information architecture and routes

| Route | Screen | Req | Phase | Cut priority |
|-------|--------|-----|-------|--------------|
| `/` | Judge Start | DEPLOY-02/03 | 4 | keep |
| `/shop` | Shopper agent | UI-01 | 2 | keep |
| `/receipts` | Receipts list | UI-02 | 3 | keep (small) |
| `/receipts/:id` | Promise Receipt + Scenario Console | UI-02, FULF-02 | 3 | keep |
| `/receipts/:id/replay` | Promise Replay | UI-03, LEDG-02 | 3 | keep |
| `/tower` | Control tower | UI-04 | 4 | keep |
| `/tower/cases/:id` | Drift review | DRIFT-01..04 | 3 | keep |
| `/proof` | Proof | PROOF-02/03 | 4 | keep |
| `/events` | Event history | LEDG | 4 | **cut first** |
| `/spine` | Spine Console (token-gated dev page) | PAY-01..06 | 1 | remove or hide in 4 |

Mapping to the mock's nav: Control tower → `/tower`; Promise receipts → `/receipts`; Drift queue → `/tower?filter=drift` (same grid, filtered; badge = open DRIFT/HOLD count); Event history → `/events`.
Routing: `createBrowserRouter` from `react-router`, `RouterProvider` from `react-router/dom` (never `react-router-dom`). Render needs a static-site rewrite of `/*` to `/index.html`.

---

## 5. Core flows

### 5.1 Happy path (the 8 demo acts)

```
/  ──Run demo scenario──▶ /shop (pre-filled instruction, still editable)
 1 Instruction ─▶ 2 Constraints ─▶ 3 Candidates ─▶ 4 Merchant quote ─▶ 5 Review & approve receipt ─▶ 6 PayPal authorization
                                                                                                           │
                                       /receipts/:id  (AUTHORIZED · NOT CAPTURED)  ◀────────────────────────┘
                                              │ Scenario Console: "Send refurbished item picked"
                                              ▼
                         Gate = DRIFT → status CAPTURE BLOCKED → /tower/cases/:id (expected vs observed)
                                              │ Scenario Console: "Send correct item + carrier accepted"
                                              ▼
                         Gate re-evaluates → MATCH → real capture → CAPTURED (+ webhook row)
                                              │
                                              ▼
                         /receipts/:id/replay  (10 steps, divergence highlighted, Verify integrity ✓)
```

### 5.2 Exception flows (each needs a designed state)

| Trigger | Screen response |
|---------|-----------------|
| LLM keys exhausted / error | Constraints chip reads **Fallback parser** (neutral), flow continues |
| Channel3 `condition: null` | Candidate row shows **UNVERIFIED**; user may still pick, receipt records it |
| Non-USD offer | Row disabled with reason "Only USD offers are supported" |
| Quote total > max | Step 5 shows **Contract rejected** block; no approve / PayPal buttons |
| Merchant changes terms after approval | Receipt banner **Stale · reapproval required**, link to new version, old version dimmed with "Superseded" |
| Approve returns 409 | Inline "This receipt changed" + "Review version N+1" |
| PayPal popup closed / declined | "PayPal approval was cancelled. Nothing was authorized." Retry button |
| Label-only carrier / late ETA / claim | Gate = HOLD (warning) with the finding; no capture |
| Auth past `expiration_time` (demo clock) | **Expired** (danger) + "Capture prohibited · renewal required" |
| Capture pending at PayPal | **Capture pending** (warning), polling continues |
| Duplicate evidence event | Toast-free inline row "Duplicate event ignored" in the evidence list |
| Server cold start | Banner + auto-retry (2, 4, 8, 16 s), skeletons stay |
| Void | Dialog with reason code → Voided (neutral); capture permanently refused |

---

## 6. Screens

Focal points: Receipt = Gate block + PayPal amount · Drift review = finding banner · Control tower = Needs attention + grid · Replay = divergence row · Shopper agent = the current step's primary action · Judge Start = Run demo scenario.

For every screen the states are: **loading** (skeletons with final geometry), **empty**, **error** (copy in UI-SPEC), **populated**. Only populated layouts are drawn below.

### 6.1 Judge Start `/` (Phase 4)

Single column, max 720 px, no hero imagery.
- Eyebrow `PROMISE-GATED PAYMENTS` · `h1` "Capture only what the buyer approved" · description (one sentence: instruction → receipt → PayPal authorization → evidence → capture or hold).
- Card **How to test (5 minutes)**: 3 numbered steps (Run the scenario · Approve with the Sandbox buyer · Send the mismatch, then the correction). Sandbox buyer credentials in a mono block with copy buttons (public Sandbox test account only).
- Primary **Run demo scenario** (creates a fresh clock-relative receipt and authorization, DEPLOY-03). Secondary links: Proof, README.
- Card **What is simulated**: three lines (merchant fulfillment, carrier events, merchant quote are synthetic; PayPal Sandbox and Channel3 data are real).
- Cold-start banner above the card when the first request is slow.

### 6.2 Shopper agent `/shop` (Phase 2, UI-01)

```
┌ Stepper rail 240 ┬ Step content (flex) ───────────────────────────┬ Promise summary 320 (sticky) ┐
│ 1 Instruction ✓  │ eyebrow STEP 2 OF 6                              │ PROMISE SO FAR                │
│ 2 Constraints ●  │ h1 Review what we understood                     │ Product —                     │
│ 3 Candidates     │ [chip AI extracted | Fallback parser]            │ Condition  New                │
│ 4 Quote          │ form: Product type · Condition (select) ·        │ Max total  $100.00 USD        │
│ 5 Approve        │ Variant/color · Max total + currency ·           │ Deadline   +5 days (resolved) │
│ 6 Authorize      │ Deliver within (days) · Substitution (switch)    │ Hash       — (after step 5)   │
│                  │ [Back to step 1]            [Search products]    │                               │
└──────────────────┴──────────────────────────────────────────────────┴───────────────────────────────┘
```
Step contents:
1. **Instruction**: textarea (prefilled example), helper "Relative dates like '5 days' are resolved by the server, not the AI." Primary **Extract constraints**.
2. **Constraints**: editable typed fields; chip states `AI extracted` (accent-soft) / `Fallback parser` (neutral). Deadline shown as resolved absolute date plus "from server clock".
3. **Candidates**: Channel3 results as a selectable list (image 48 px, title, brand, price, condition badge, merchant domain). Selecting a row expands variant radio group (Color etc.). Raw-snapshot note: "Stored exactly as received (sha256 …)".
4. **Merchant quote**: card with seller, item, shipping, tax, **total**, promised delivery, caption "Sandbox stand-in for `<domain>`. Checkout total confirmed separately from catalog price."
5. **Review & approve**: the receipt preview (frozen constraints, product + variant, quote, capture conditions, hash). Primary **Approve receipt `sha256:8f3b…9d1a`**. Rejected state replaces the primary with the error block.
6. **Authorize**: only after approval. Amount Display, PayPal button (v6 per STACK; v5 fallback behind the same `<PayPalAuthorizeButton>` wrapper), caption "Authorized, not captured. Not an escrow service." On success show the IDs card (order ID, authorization ID, expires) and **Open promise receipt**.

Navigation: completed steps are clickable until step 5 is approved; after approval, steps 1–5 become read-only.

### 6.3 Promise Receipt `/receipts/:id` (Phase 3, UI-02) — matches mock 3

```
header: eyebrow PURCHASE RECORD · VERSION 1 · h1 Promise Receipt · desc            [Open drift review]
┌ Receipt card (flex) ───────────────────────────────────┐ ┌ PayPal transaction 360 ──────────────┐
│ PROMISE RECEIPT · PL-8F3B2C        [Authorized · not captured] │ $89.99 (Display) USD · Sandbox │
│ h2 Wireless headphones   Created … · Demo Merchant A   │ │ Order ID      3KX…  [copy]          │
│ ─ ORIGINAL BUYER INSTRUCTION ─────────────────────────│ │ Authorization 9K31… [copy]          │
│ “Find new black over-ear …”   [AI extracted][Buyer confirmed] │ Payment state  Authorized     │
│ ─ FROZEN PURCHASE CONSTRAINTS (2×3 grid) ─────────────│ │ Capture        Not submitted        │
│ Product · Variant · Condition · Max total · Merchant · Delivery │ warning strip: Authorized, not captured. Not an escrow service. │
│ ─ GATE (latest decision) ─ Verified | finding + explanation │ ┌ Evidence sources ────────────────┐
│ ─ PROMISE LIFECYCLE ──────────────────────────────────│ │ Buyer instruction   Confirmed     │
│ ✓ Buyer instruction approved  time · source           │ │ Product snapshot    Stored        │
│ ✓ Product and merchant offer selected                 │ │ Merchant promise    Stored        │
│ ✓ PayPal authorization created · AUTH id · $89.99     │ │ Fulfillment events  Mismatch      │
│ ✕ Fulfillment mismatch detected (danger)              │ └───────────────────────────────────┘
└───────────────────────────────────────────────────────┘ ┌ Receipt integrity ───────────────────┐
┌ Evidence list (below, full width) ────────────────────┐ │ sha256:8f3b…9d1a [copy] · version 1 │
│ #  Source  Type  Trust badge  SYNTHETIC  Observed  Time │ │ custom_id anchor: matches ✓         │
└────────────────────────────────────────────────────────┘ │ caption: protects the snapshot …    │
┌ Scenario Console · SYNTHETIC (amber outline) ─────────────┘ [Verify integrity]  [Open replay]  └─
```
- Header status pill (UI-02): **AUTHORIZED · NOT CAPTURED** (warning) / **CAPTURE BLOCKED** (danger) / **CAPTURED** (success), always uppercase; STALE adds a full-width warning banner.
- Lifecycle uses state glyphs: done (success check), current (accent ring), failed (danger cross), pending (hollow neutral). Each line: title, `HH:MM:SS · source`, optional mono ID.
- Gate block: deterministic finding first (code in mono), then "Explanation (AI or template)" paragraph below, muted.
- Evidence rows: trust ladder badge (`merchant_system`, `carrier` neutral; `claim` warning "can only hold"), `SYNTHETIC`, source, ingestion seq, observed value, receipt-expected value on mismatch.
- Scenario Console buttons: Send refurbished item · Send wrong color · Send correct item + carrier accepted · Send label only (no carrier scan) · Send late ETA · Replay duplicate event · Merchant changes price · Advance demo clock +30 days. Disabled with tooltip when the state makes them meaningless (e.g. after capture).

### 6.4 Drift review `/tower/cases/:id` (Phase 3) — matches mock 2

```
header: EXCEPTION REVIEW · PL-8F3B2C · h1 Promise drift review · desc                  [CAPTURE BLOCKED]
┌ Finding banner (danger tint) ───────────────────────────────┐ ┌ AVAILABLE ACTIONS ───────────────┐
│ h2 Product condition does not match buyer approval [Critical mismatch] │ [Send corrected item]  (secondary, labeled SYNTHETIC) │
│ Order … · product · Detected …                              │ │ [Re-run promise checks] (secondary) │
├ EVIDENCE COMPARISON ────────────────────────────────────────┤ │ [Void authorization…] (danger outline) │
│ ┌ BUYER-APPROVED (success tint) ┐ ┌ FULFILLMENT PICKED (danger tint) ┐ │ warning note: Capture remains blocked until │
│ │ New     source: Receipt v1    │ │ Refurbished   source: adapter · EVT-0192 │ │ corrected evidence passes revalidation.   │
├ ENGINE FINDING (code, plain explanation) ───────────────────┤ ├ PROMISE DRIFT ENGINE ─────────────┤
├ POLICY EVALUATION (key/value rows) ─────────────────────────┤ │ Rule · Result · Required action ·   │
├ DECISION HISTORY (time · text, tone-colored) ───────────────┘ │ Financial control: Deterministic     │
                                                                 │ "No LLM response can override this rule." │
```
- Show **all** findings (rules never short-circuit): primary finding large, others as a compact list below it.
- The mock's "Simulate corrected item" is renamed **Send corrected item** inside a SYNTHETIC-labeled group; it posts evidence, it does not "fix" anything by itself.
- "Re-run promise checks" re-evaluates and shows an inline result row (MATCH / unchanged), never a silent refresh.
- "Void authorization…" opens the destructive dialog (§8).

### 6.5 Promise Replay `/receipts/:id/replay` (Phase 3, UI-03, LEDG-02)

One screen at 1280×800: ten rows of 56 px (560 px) plus header.
```
header: eyebrow AUDIT TIMELINE · h1 Promise Replay                 [Verify integrity] [Download JSON]
┌ Timeline (flex) ─────────────────────────────────────────────────────┐ ┌ Integrity 320 ─────────┐
│ ① Instruction received   source · time   ID/hash chip                │ │ Chain  ✓ intact · 27 ev │
│ ② Products discovered     Channel3 · snapshot sha256:…               │ │ Artifacts verified 3/3  │
│ ③ Product selected        …                                          │ │ PayPal anchor           │
│ ④ Merchant promise recorded  Sandbox stand-in …                      │ │ custom_id = purchase:hash ✓ │
│ ⑤ Receipt approved        receipt sha256:8f3b…9d1a · v1              │ │ Honest limit (caption)  │
│ ⑥ PayPal order authorized order ID · AUTH id · $89.99                │ └─────────────────────────┘
│ ⑦ Evidence recorded       SYNTHETIC · EVT-0192                       │
│ ⑧ Drift evaluated  ◀ DIVERGENCE (danger tint, expected vs observed inline)
│ ⑨ Remedy                  deterministic code → remedy (+ labeled prose) │
│ ⑩ Capture result + webhook  capture ID · PAYMENT.CAPTURE.COMPLETED   │
└──────────────────────────────────────────────────────────────────────┘
```
- Each row: step number badge, name, source, timestamp (mono), PayPal ID chip, hash chip. Multi-event steps (e.g. blocked then corrected evaluations) show a count and expand inline; the divergence step is expanded by default.
- **Verify integrity** → `✓ Chain intact · N events` or `Broken at event #K` (the broken row gets a danger outline).
- Timestamps use `occurred_at` (clock-aware); `recorded_at` on hover. Simulated offset shown in the chip.

### 6.6 Control tower `/tower` (Phase 4, UI-04) — matches mock 1

- Header: eyebrow `COMMERCE ACCOUNTABILITY`, `h1` Control tower, actions **Refresh data** (secondary) and **Run demo scenario** (primary; replaces the mock's "Create receipt +").
- 4 KPI cards: Active promises · Verified outcomes (% of active) · Review required (open capture holds) · Authorized · not captured (sum, count of open authorizations). Values are computed from the real tables; never typed in.
- Two panels: **Recent promises** (last 4, "View all" → `/receipts`) and **Needs attention** (open DRIFT/HOLD cases with icon, title, ref, short reason, amount · status; "Open drift queue").
- **Drift cases grid** (AG Grid Community, full width, 10 rows visible, pagination off):

| Column | Content |
|--------|---------|
| Promise | `PL-8F3B2C`, link to receipt |
| Product | title · variant · condition |
| Amount | tabular, USD |
| **Authorization** | pill (UI-SPEC vocabulary) |
| **Gate** | pill + finding code |
| Auth expiry | countdown `2d 4h` (warning < 24 h, danger when expired), sorted ascending by default |
| Evidence | count + SYNTHETIC |
| Updated | relative time |
| Actions | Reconcile with PayPal (secondary, small) · Void authorization… (danger outline, small) |

  Theme via the Theming API (`themeQuartz.withParams({...})`; confirm param names against v36 docs when building): font Inter 14, row height 56, header background `--color-inset`, header text Label style, borders `--color-line`, accent `--color-accent`, no row striping, wrapper radius 12. Register modules with `<AgGridProvider modules={[AllCommunityModule]}>`. Row click opens Drift review; Actions column stops propagation.
- Event history strip (last 5 events) at the bottom with "View all" → `/events`.

### 6.7 Proof `/proof` (Phase 4, PROOF-02/03)

- Six metric cards, each **numerator / denominator** large and the plain-English definition beneath: Detection rate (e.g. `9 / 9`), Unsafe-capture prevention, False-block rate, Decision latency (p50 / p95 ms), Duplicate actions prevented, Expiry handling. Source line: "15–20 labeled scenarios · run N · commit abc123".
- Table of scenarios: ID · label · expected outcome · actual outcome · codes · pass/fail pill.
- **Proves / does not prove** two-column card. Does-not-prove includes: external events are true, real carrier integration, production fraud reduction.
- AP2 v0.2 mapping and OSS licence as links. No charts are required; do not add decorative ones.

### 6.8 Event history `/events` (P1)

Single table: time (mono) · event type · promise · source · actor · result pill · hash chip, filter by promise, "Verify integrity" per promise. Same empty/error states.

### 6.9 Receipts list `/receipts`

Same table as "Recent promises" with all rows, status columns (Authorization + Gate), search by ref, newest first.

### 6.10 Spine Console `/spine` (Phase 1)

Dev-only and token-gated; ugly-but-honest is acceptable, built from shell + Card + Button + HashChip. Sections: **Authorize** (amount input, PayPal button), **State** (order ID, auth ID, `expiration_time`, state), **Capture / Void** (token-gated dev buttons; void requires a reason code), **Webhook log** (event ID, type, verified/rejected, stored once), **Ledger tail**. Remove or 404 it in production at Phase 4 (SEC-01: no public capture/void).

---

## 7. Component inventory

Build in `src/components/ui/` first, then composites. Props are the contract; keep each file small.

| Component | Variants / props | Notes |
|-----------|------------------|-------|
| `Button` | `variant: primary \| secondary \| danger \| ghost`, `size: sm(32) \| md(40)`, `loading`, `icon` | Primary = accent fill white text; secondary = white + `line-strong` border; danger = white + bad border/text, filled `bad` only inside the confirm dialog |
| `Badge` / `StatusPill` | `tone: ok \| warn \| bad \| neutral \| info`, `uppercase`, `icon?` | Pill, Label type, tint + 1 px line. Single mapper `statusToPill()` implements the UI-SPEC vocabulary, so no screen hand-picks tones |
| `Card` | `title`, `subtitle`, `action`, `tone?: default \| bad \| warn` | 12 px radius, 1 px `line`, `--shadow-card`, padding 24 |
| `PageHeader` | `eyebrow`, `title`, `description`, `actions`, `status?` | |
| `StatCard` | `label`, `value`, `caption`, `tone` | KPI Display value, tabular |
| `KeyValueRow` / `KeyValueGrid` | `label`, `value`, `mono?`, `copy?` | Hairline-separated rows (Policy evaluation, PayPal card) |
| `HashChip` / `IdChip` | `value`, `kind: sha \| paypal \| evt`, `copy` | Mono, `8…4` truncation, tooltip full value, copy with `aria-live` "Copied" |
| `Stepper` | `steps[]`, `current`, `onSelect`, `locked` | Vertical rail; states done / current / upcoming |
| `Timeline` / `LifecycleStep` | `state: done \| current \| failed \| pending` | Glyph + title + meta |
| `ReplayStep` | `n`, `title`, `source`, `at`, `ids[]`, `hash`, `divergence?` | Expandable |
| `EvidenceCompare` | `expected`, `observed`, `sources` | Two tinted cards, success vs danger |
| `FindingBanner` | `code`, `title`, `severity`, `explanation` | Code mono; explanation labeled "Explanation (AI or template)" |
| `TrustBadge` | `trust: merchant_system \| carrier \| claim`, `synthetic` | |
| `Banner` | `tone`, `title`, `body`, `action` | Cold start, simulated clock, API down |
| `ConfirmDialog` | `title`, `body`, `confirmLabel`, `cancelLabel`, `destructive`, `children` | Focus trap, Esc, restores focus |
| `Skeleton` | `lines`, `block` | Final geometry, no shimmer gradient (plain 1.2 s opacity pulse, off for reduced motion) |
| `EmptyState` | `title`, `body`, `action` | |
| `DataTable` | static semantic `<table>`, sticky header, `onRowClick` | For Recent promises, Evidence, Events (AG Grid only for the tower) |
| `Field`, `Select`, `Switch`, `Textarea` | `label`, `hint`, `error` | Label above, error below with `aria-describedby` |
| `PayPalAuthorizeButton` | `receiptId`, `onAuthorized`, `onCancel` | Wraps SDK; the only file importing `@paypal/react-paypal-js` |

Icons (lucide, stroke 1.5): `layout-grid`, `file-text`, `triangle-alert`, `activity`, `shopping-bag`, `shield-check`, `octagon-alert`, `check`, `x`, `copy`, `clock`, `refresh-cw`, `external-link`, `chevron-right`. Decorative icons `aria-hidden`; icon-only buttons get `aria-label`.

---

## 8. Key interaction details

**Void dialog**
- Title "Void authorization", body per UI-SPEC copy with the real amount, required **Reason** select (`Cancelled by buyer · Out of stock · Contract violation · Other`), buttons **Void authorization** (danger fill, disabled until reason chosen) / **Keep authorization**. After success: Authorization pill → Voided; Scenario Console and void button disabled with tooltip "Authorization is voided".

**Approve receipt**
- Optimistic UI is forbidden. Button shows loading, then the PayPal step unlocks only on a 2xx that echoes the approved hash.

**Scenario action**
- Click → button loading → inline result row under the console: "Evidence EVT-0192 recorded · Gate: Condition mismatch". Gate pill and lifecycle update from the refetch, not from local state.

**Copy**
- Copy button swaps its icon to `check` for 1.5 s and announces "Copied" via `aria-live="polite"`.

**Empty vs not-yet**
- "Awaiting evidence" (neutral) is a valid Gate value, not an empty state.

---

## 9. Data layer

```
src/lib/api.ts        fetch wrapper: base URL from VITE_API_URL, JSON, typed errors, cold-start retry (2/4/8/16 s)
src/lib/money.ts      formatMinor(minor: number, currency: string): string  (Intl; reject non-integers)
src/lib/status.ts     statusToPill(): authorization / gate / receipt vocabulary (single source)
src/lib/time.ts       relative(), countdown(), mono timestamp; applies demo-clock offset label
src/queries/*.ts      useReceipt, useReplay, useTower, useEvents, useProof (TanStack Query hooks)
```

- Query keys: `['receipt', id]`, `['replay', id]`, `['tower']`, `['events', filter]`, `['proof']`.
- Polling: `refetchInterval` returns 3000 while `payment.state ∈ {capturing, capture_pending, voiding}` or the last mutation is in flight, otherwise `false`; Tower 10000; `refetchIntervalInBackground: false`.
- Mutations invalidate `['receipt', id]`, `['replay', id]`, `['tower']`.
- Types are hand-written to start (about 10 interfaces). If shapes churn, generate with `openapi-typescript` from `/openapi.json`.
- Frontend never holds PayPal secrets; the only PayPal value in the browser is the public client ID and order IDs returned by the server. **No** call to any LLM or PayPal REST API from the browser.

Endpoints the UI expects (names are **proposals** for the backend phases to confirm; `/purchases/{id}/replay` is the one named in ARCHITECTURE.md):

| UI need | Proposed endpoint |
|---------|-------------------|
| Run demo scenario | `POST /demo/scenarios` → `{purchase_id}` |
| Extract constraints | `POST /shopper/extract` |
| Search / select / quote | `POST /shopper/search` · `POST /purchases/{id}/select` · `GET /purchases/{id}/quote` |
| Compile + approve receipt | `POST /purchases/{id}/receipt` · `POST /receipts/{id}/approve {content_hash}` |
| Create order / authorize | `POST /checkout/orders` · `POST /checkout/orders/{id}/authorize` |
| Receipt view | `GET /receipts/{id}` |
| Replay + verify | `GET /purchases/{id}/replay` · `POST /purchases/{id}/verify` |
| Evidence (Scenario Console) | `POST /fulfillment/scenarios/{id}/{scenario}` |
| Operator actions | `POST /purchases/{id}/void {reason}` · `POST /purchases/{id}/reconcile` |
| Tower / events / proof | `GET /tower` · `GET /events` · `GET /proof` |

---

## 10. Reference conformance and corrections

The three mocks are the visual target. Match: sidebar width and nav styling, page-header pattern, white cards with hairline borders, uppercase Label eyebrows and table headers, pill badges, key/value rows, red/green evidence cards, the two-column receipt layout and the integrity block.

Corrections to apply (do not copy these mock defects):

| Mock issue | Fix |
|------------|-----|
| "Needs attention" icons render as a stray "·" | Real lucide icons in 32 px tinted squares |
| Receipt "Merchant / Delivery commitment" row is clipped by the section divider | Grid rows with 24 px bottom padding; section dividers belong to the section |
| Lifecycle markers are all hollow circles | Done ✓, current ring, failed ✕, pending hollow |
| "Create receipt +" in Control tower | "Run demo scenario"; receipts come from the shopper flow |
| Sequential ids `PL-00842` | `PL-` + first 6 hex of purchase UUID (invoice IDs must be unique per merchant; a counter collides after a DB reset) |
| "Simulate corrected item" | **Send corrected item**, inside the SYNTHETIC console |
| Hash shown with "· DEMO" | Real hash; "DEMO" is not a hash qualifier. Sandbox is already labeled in the topbar |
| Merchant "Northstar Commerce" / product names differ between screens | One consistent demo merchant and product per purchase across every view |
| KPI strings hand-typed ("81.3% of active promises") | Always derived from data |
| No expiry visibility in the grid | Add the Auth expiry countdown column |
| Authorization and Gate not separated in the Tower table | Two columns (UI-SPEC vocabulary) |

---

## 11. Accessibility and responsive

- Contrast verified: ink 17.9, muted 5.9 (5.5 on canvas), accent 5.2, ok 4.8, warn 4.7, bad 5.9, neutral 6.9. Do not use `#8A94A6` for text.
- Focus ring 2 px accent; tab order follows reading order; dialogs trap and restore focus; every pill has text; DRIFT adds an icon and the code.
- `role="status"` for gate and capture result changes, `role="alert"` for errors; AG Grid keeps native keyboard behavior; header cell tooltips for truncated text.
- Reduced motion honored globally (token CSS).
- Breakpoints: **≥1280** full layout; **768–1279** sidebar collapses to a 64 px icon rail, right columns drop below main; **<768** sidebar becomes a top drawer, summary columns stack above content, cards full-bleed with 16 px gutters, tables and the grid scroll horizontally inside their card; minimum width 360. Touch targets ≥ 40 px on mobile. No horizontal page scroll.

---

## 12. File structure

```
frontend/src/
  main.tsx                RouterProvider, QueryClientProvider, AgGridProvider
  index.css               tokens (section 2)
  routes.tsx              route table (section 4)
  components/ui/          Button, Badge, Card, PageHeader, StatCard, KeyValue, HashChip, Banner,
                          ConfirmDialog, Skeleton, EmptyState, DataTable, Field...
  components/domain/      StatusPill (via status.ts), EvidenceCompare, FindingBanner, TrustBadge,
                          Stepper, Timeline, ReplayStep, ScenarioConsole, PayPalAuthorizeButton
  layout/                 AppShell, Sidebar, Topbar, Banners
  pages/                  Start, Shop/{steps}, Receipt, Receipts, Replay, Tower, DriftReview, Proof, Events, Spine
  lib/                    api.ts, money.ts, status.ts, time.ts
  queries/                one hook per resource
  types/                  api.ts
```
Delete `App.css`, `assets/hero.png`, `react.svg`, `vite.svg`, the template counter UI and `public/icons.svg` when the shell lands.

---

## 13. Build order (aligned to roadmap)

| Phase | Frontend deliverable | Exit check |
|-------|----------------------|------------|
| 1 (by Nov 2) | Tokens + AppShell + `Button/Card/HashChip` + `/spine` with PayPal button, IDs, webhook log | From the Render URL: approve in the popup, see order/auth ID and `expiration_time`; `npm run build` + `npm run lint` clean |
| 2 | `/shop` six steps, Stepper, Field set, candidate list, quote card, receipt preview, `PayPalAuthorizeButton` | Whole flow works with LLM keys disabled (Fallback chip); over-limit shows rejected block with no PayPal button; 409 state reachable |
| 3 | `/receipts/:id`, Scenario Console, `/tower/cases/:id`, `/receipts/:id/replay`, status vocabulary, polling | Refurbished → CAPTURE BLOCKED with expected/observed → corrected → CAPTURED; Replay shows 10 steps on one 1280×800 screen; Verify integrity both outcomes |
| 4 | `/` Judge Start, `/tower` with AG Grid + KPIs, `/proof`, banners (cold start, clock), a11y and responsive pass; `/events` only if time | Fresh incognito run from the README alone (S1–S7 in USER-RESEARCH); 375 / 768 / 1280 screenshots clean |

Cut order if behind (UI only): `/events` → Receipts list (reuse Tower panel) → Proof charts (none planned) → mobile polish below 768. **Never cut:** status vocabulary, Receipt, Drift review, Replay, SYNTHETIC labels, cold-start banner.

---

## 14. Verification (what "done" means)

Run per phase (narrowest first, full gate once at the end):
1. `npm run build` (runs `tsc -b`) and `npm run lint` (oxlint) in `frontend/`.
2. In the browser pane, at 1280, 768 and 375 widths: each screen in populated, loading (throttled), empty and error states. Confirm no horizontal page scroll, no layout shift on poll, focus order, and that every Don't in UI-SPEC holds.
3. Contract spot checks by search: no `#000`, no `shadow-lg`/`shadow-xl`, no `gradient`, no `dark:`, no emoji characters, no `"Paid"` / `"Escrow"` strings, only font sizes 12/14/18/28, only weights 400/600.
4. Content checks: Authorized never green; condition `null` never "New"; every simulator row shows SYNTHETIC; one primary button per region.
5. Usability sessions per `.planning/ui/USER-RESEARCH.md` §4–5 after Phase 3; fix every S3, S6, S7 failure before submission.
6. `bash scripts/verify.sh` once at Finalize.

Not verified yet: nothing in this document has been rendered; the proposed endpoints do not exist; AG Grid 36 theming parameter names and PayPal v6 button behavior must be confirmed against current docs during build.
