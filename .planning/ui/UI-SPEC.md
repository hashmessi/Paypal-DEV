---
phase: ui (cross-cutting: Phase 1 spine console, Phase 2, Phase 3, Phase 4)
slug: promiseloop-ui
status: approved
reviewed_at: 2026-11-01
shadcn_initialized: false
preset: none
created: 2026-11-01
---

# PromiseLoop — UI Design Contract

> Visual and interaction contract for every frontend phase. Locks tokens, vocabulary and copy so no phase
> invents styling. Build guide with layouts, flows and components: `frontend/UI.md`.
> Research basis (hypotheses): `.planning/ui/USER-RESEARCH.md`.
> Visual reference: the three approved mock screens (Control tower, Promise drift review, Promise Receipt).

**Requirement coverage:** UI-01 (Phase 2), UI-02, UI-03 (Phase 3), UI-04 (Phase 4), FULF-02 console (Phase 3),
PROOF-02 page and DEPLOY-02/03 notices (Phase 4), PAY-01 approve page (Phase 1).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (hand-built components on Tailwind v4 tokens; shadcn **not** used) |
| Preset | not applicable |
| Component library | none; AG Grid Community 36.2.0 for the Control Tower grid only |
| Icon library | lucide-react (tree-shaken, stroke 1.5, 16/20 px). New dependency, justified: one consistent a11y-safe icon set vs hand-drawing ~14 SVGs. Pin at install after `npm view`. |
| Font | Inter (UI) and JetBrains Mono (IDs, hashes, timestamps in ledger), self-hosted via `@fontsource-variable/*` so Render needs no external font host |
| Theme | **Light only.** No dark mode, no `prefers-color-scheme` branch. |
| Router / data | React Router 8 data mode (`react-router`, `react-router/dom`), TanStack Query 5 polling |

---

## Spacing Scale

All values multiples of 4.

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gaps, badge inner gap |
| sm | 8px | Compact stacks, badge padding-y, button icon gap |
| md | 16px | Default gap, card row padding-y, input padding-x |
| lg | 24px | Card padding, section gap inside a page |
| xl | 32px | Page gutter (desktop), gap between cards |
| 2xl | 48px | Major section breaks |
| 3xl | 64px | Empty-state vertical padding |

Sanctioned layout constants (all multiples of 4): control heights 32 / 40 px (`sm` buttons become 40 px below
768 px); sidebar 232 (icon rail 64); topbar 64; table row 56; stepper rail 240; summary column 320; PayPal card 360;
Judge Start max width 720; page max width 1280; thumbnail 48. Non-spacing exceptions: 2 px focus ring and offset,
1 px borders. No other exceptions. Radius: 8 (controls), 12 (cards), 999 (badges).

---

## Typography

Four sizes, two weights (400, 600).

| Role | Size | Weight | Line Height | Used for |
|------|------|--------|-------------|----------|
| Body | 14px | 400 | 1.5 | Paragraphs, table cells, form values |
| Label | 12px | 600 | 1.33 | Eyebrows (uppercase, +0.04em), table headers, badges, helper text (400) |
| Heading | 18px | 600 | 1.33 | Card titles, finding titles, dialog titles |
| Display | 28px | 600 | 1.2 | Page `h1`, KPI numbers, PayPal amount |

Mono (JetBrains Mono): 12 / 14 px, weight 400, for PayPal IDs, hashes, request IDs, ledger seq.
Numerals in tables and KPIs use `font-variant-numeric: tabular-nums`.

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `#FFFFFF` | Cards, sidebar, topbar, inputs |
| Secondary (30%) | `#F6F7FB` canvas, `#F8FAFC` table-header / inset, `#E5E7EB` borders | Page background, table header row, dividers |
| Accent (10%) | `#2563EB` (hover `#1D4ED8`, soft `#EFF6FF`) | See reserved list below |
| Text | `#0F172A` primary, `#596579` muted | |
| Destructive | `#B91C1C` on `#FEF2F2` | Void authorization, DRIFT / mismatch status only |

Status tones (text on tint, all measured ≥ 4.5:1):
success `#15803D` / `#ECFDF3` (4.76), warning `#B45309` / `#FFF7E6` (4.71), danger `#B91C1C` / `#FEF2F2` (5.91),
neutral `#475569` / `#F1F5F9` (6.92), info `#1D4ED8` / `#EFF6FF` (6.16). White on accent 5.17; white on danger 6.47.
`#8A94A6` (3.06) is **not** allowed for text.

Accent reserved for: primary button fill, active nav item, text links, focus ring, logo mark, the **AI extracted**
chip, selected stepper step, current lifecycle step ring, selected grid row indicator, and the **info** tone
(`#1D4ED8` on `#EFF6FF`) used only for in-flight states (Capturing). Never for: success/failure meaning,
decorative fills, icons in cards, headings.

Supporting neutrals (sanctioned, not accents): `--line-strong #D1D5DB` (secondary button / input borders); status
borders ok `#BBF7D0`, warn `#FDE7B0`, bad `#FECACA`, neutral `#E2E8F0`. "Destructive" means the **danger tone**:
Void authorization, DRIFT / mismatch, Expired, Failed, Rejected, drift-queue count badge, expired countdown.

---

## Status Vocabulary (single source of truth)

Two orthogonal facts, never merged into one pill (architecture decision: "held" is not a payment state).

| Fact | Source | Values → label · tone |
|------|--------|----------------------|
| **Authorization** (money truth, mirrors PayPal) | `payment.state` | created → Order created · neutral; approved → Approved · neutral; authorized → **Authorized · not captured** · warning; capturing → Capturing · info; capture_pending → Capture pending · warning; captured → **Captured** · success; voided → Voided · neutral; expired → Expired · danger; failed → Failed · danger |
| **Gate** (latest drift decision) | `decision.outcome` + finding code | MATCH → **Verified** · success; DRIFT → `<Finding label>` · danger (e.g. "Condition mismatch"); HOLD → `<Finding label>` · warning (e.g. "Awaiting carrier"); PROHIBITED → Capture prohibited · danger; none yet → Awaiting evidence · neutral |
| **Receipt** | `receipt.status` | draft → Draft · neutral; approved → Approved · success; stale → **Stale · reapproval required** · warning; superseded → Superseded · neutral; rejected → Rejected · danger |
| **Promise state** (Receipt page header only, UI-02) | derived | AUTHORIZED · NOT CAPTURED / **CAPTURE BLOCKED** / CAPTURED (uppercase; wording fixed by UI-02). All other pills render sentence case as written. |

Fixed caption wherever Authorized appears with a dollar amount: "Authorized, not captured. Not an escrow service."
Evidence badges: `SYNTHETIC` (warning outline) on every simulator row; trust ladder `merchant_system` / `carrier`
(neutral) vs `claim` (warning, "can only hold"). Condition `null` → `UNVERIFIED` (warning), never "New".

---

## Screens and Routes

| Route | Screen | Req | Phase |
|-------|--------|-----|-------|
| `/` | Judge Start (what it is, 3-step guide, **Run demo scenario**, cold-start notice) | DEPLOY-02/03 | 4 |
| `/shop` | Shopper agent (6-step flow) | UI-01, INTENT, DISC, RCPT-03, PAY-01 | 2 |
| `/receipts` | Promise receipts list | UI-02 | 3 |
| `/receipts/:id` | Promise Receipt (+ Scenario Console panel) | UI-02, FULF-02 | 3 |
| `/receipts/:id/replay` | Promise Replay (10 steps, Verify integrity) | UI-03, LEDG-02 | 3 |
| `/tower` | Control tower overview (KPIs, recent, needs attention, AG Grid) | UI-04 | 4 |
| `/tower/cases/:id` | Drift review (expected vs observed, engine finding, actions) | UI-04, DRIFT | 3 (view) / 4 (grid entry) |
| `/events` | Event history (cross-purchase ledger feed) | LEDG | 4 (P1; cut first) |
| `/proof` | Proof (metrics with numerator/denominator, scenario table, proves / does-not-prove) | PROOF-02/03 | 4 |
| `/spine` | Spine Console, token-gated dev page: authorize, capture, void, webhook log | PAY-01..06 | 1 (hidden or removed in 4) |

Shell: left sidebar (Control tower, Promise receipts, Drift queue + count badge, Event history; Shopper agent and
Proof appear under a second group "Demo"), topbar with breadcrumb, **SANDBOX ENVIRONMENT** pill, demo-clock chip.

---

## Focal Points (one per screen)

Receipt: Gate block + PayPal amount · Drift review: finding banner · Control tower: Needs attention + grid ·
Replay: divergence row · Shopper agent: current step's primary action · Judge Start: Run demo scenario.

---

## Interaction Contracts

1. **Money-moving controls** exist only as: PayPal approval button (buyer), **Void authorization** (operator, reason
   required), **Reconcile** (read-only GET). There is no "Capture" button anywhere. Capture is the gate's outcome.
2. **Scenario console** is a panel titled "Scenario console · SYNTHETIC", amber outline, one button per scenario.
   Caption: "Sends simulated fulfillment evidence. Does not execute payments." Buttons are labeled by the evidence
   they send, not by the result they cause.
3. **Approve receipt**: button text "Approve receipt `sha256:8f3b…9d1a`". Server 409 → inline error "This receipt
   changed. Review version N+1." with a button that loads it. The PayPal button is not rendered until approved.
4. **Rejected contract** (total > max): no approve button, no PayPal button; error block states total vs limit.
5. **Void dialog**: reason code select is required; confirm button disabled until chosen.
6. **Verify integrity**: shows spinner ≤ 1 s, then `✓ Chain intact · N events` (success) or `Broken at event #K` (danger).
   (The check glyph is typographic text, not an emoji.)
7. **Polling**: Receipt / Replay refetch every 3 s only while payment state ∈ {capturing, capture_pending, voiding}
   or an evaluation is in flight; Tower every 10 s; always show "Updated Ns ago". Pause when tab hidden.
8. **Cold start**: if the first API call exceeds 3 s show the banner "Waking the sandbox server. This can take up to
   a minute on the free tier." with automatic retry (2, 4, 8, 16 s). Never an empty or spinner-only page.
9. **Demo clock**: when offset ≠ 0, a persistent warning chip "Simulated time +30d" in the topbar and on every
   timestamp tooltip. Real `recorded_at` available on hover.
10. **Hashes / IDs**: mono, truncated `8…4` with copy button and full value in a tooltip; never wrapped mid-token.
11. **Money**: formatted from integer minor units with `Intl.NumberFormat`; floats are never parsed, summed or
    displayed. Currency always shown next to totals on Receipt and PayPal cards.

---

## Copywriting Contract

Sentence case. Plain verbs. No exclamation marks, no emoji, no "AI-powered", no "seamless".

| Element | Copy |
|---------|------|
| Primary CTA (Judge Start) | Run demo scenario |
| Primary CTA (Shopper, step 1) | Extract constraints |
| Primary CTA (receipt) | Approve receipt `sha256:…` |
| Primary CTA (Tower header) | Run demo scenario (replaces the mock's "Create receipt"; receipts originate from the shopper flow) |
| Secondary | Refresh data · Re-run promise checks · Verify integrity · Reconcile with PayPal |
| Empty: Tower / receipts | **No promises yet** / Run the demo scenario to create a receipt, an authorization and the first evidence. |
| Empty: Drift queue | **No open drift cases** / Every authorization with evidence currently matches its receipt. |
| Empty: Events | **No events recorded** / Events appear as soon as a promise is created. |
| Error (API) | **Couldn't load this promise.** The server didn't respond. Retry, or check that the sandbox server has finished waking up. |
| Error (PayPal popup closed) | **PayPal approval was cancelled.** Nothing was authorized and no money moved. Approve again to continue. |
| Error (409 stale hash) | **This receipt changed.** The merchant updated its terms. Review version N+1 before approving. |
| Error (rejected) | **Contract rejected.** Merchant total $X is above your $Y limit. No PayPal request was made. |
| Blocked state | **Capture blocked.** Fulfillment evidence doesn't match the receipt you approved. The authorization stays open. |
| Destructive confirmation | **Void authorization:** This releases the $89.99 hold on the buyer's PayPal account. A voided authorization can never be captured. This cannot be undone. Buttons: `Void authorization` / `Keep authorization` |
| Synthetic notice | Simulated merchant and carrier data. The product verifies what it is given; it does not prove external events happened. |
| Hash caption | The hash protects the snapshot, not external truth. |
| Cold start | Waking the sandbox server. This can take up to a minute on the free tier. |

---

## Accessibility and Responsive

- WCAG 2.2 AA: contrast table above; visible 2 px accent focus ring offset 2 px on every focusable; target size ≥ 32 px.
- Status never by color alone: every pill carries text, and DRIFT also carries an icon (`octagon-alert`) and the finding code.
- Keyboard: full tab order; dialogs trap focus and restore it; Esc closes; AG Grid uses its native keyboard model.
- Live regions: gate result and capture result announced with `role="status"`; errors with `role="alert"`.
- `prefers-reduced-motion`: no transitions beyond 120 ms opacity; no animated counters.
- Breakpoints: ≥ 1280 primary; 768–1279 sidebar collapses to icons; < 768 sidebar becomes a top drawer, two-column
  layouts stack (summary first), tables and the AG Grid scroll horizontally inside their card (no card-list
  fallback is built). Minimum supported width 360 px.

---

## Don'ts (binding; checker and reviewer cite these)

1. No dark theme, dark AI gradients, glassmorphism, blur, neon, glow, mesh backgrounds, 3D, illustrations or robots.
2. No emoji anywhere (UI, copy, commit-visible strings). Glyph characters `✓ …` allowed only as typographic marks.
3. Shadows: none by default; max `0 1px 2px rgb(15 23 42 / 0.04)` on cards. No drop shadows on buttons or badges.
4. No more than one primary (blue-filled) button per view region.
5. No gradient fills, no colored card borders except status banners (1 px tint) and the Scenario Console amber outline.
6. No LLM text in a decision position. Explanations are captioned "Explanation (AI or template)" and sit below the
   deterministic finding. UI never says "AI approved / decided / verified".
7. Never display "Paid", "Settled" or "Secured" for an authorization. Never "Escrow".
8. Never show condition `null` as New; never hide `SYNTHETIC`.
9. No capture or void control reachable without the documented guards; no hidden admin buttons in production.
10. No placeholder-as-label inputs, no icon-only buttons without `aria-label`, no color-only status.
11. No `…` loading text in place of skeletons; no layout shift on poll updates (reserve row heights).
12. No dead UI from the mock: icons must render (the mock's "Needs attention" icons collapsed to "·"), IDs are not
    sequential counters (use `PL-` + first 6 hex of the purchase UUID), data is internally consistent across screens
    (same product, amount, IDs in the Tower, Drift review and Receipt for one purchase), no clipped rows
    (the mock's Merchant row is cut by a divider), and lifecycle steps show a state glyph (done, current, failed).
13. No fake data in production routes: seeded rows are real runs of "Run demo scenario" (DEPLOY-03).

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn | none | not applicable (not initialized) |
| npm: `lucide-react`, `@fontsource-variable/inter`, `@fontsource-variable/jetbrains-mono` | icons, fonts | verify package, publisher and version with `npm view` at install; lockfile commit |
| npm: `ag-grid-community`, `ag-grid-react` | Control Tower grid | already in `package.json`; keep the two versions identical |
| Third-party UI registries | none | none permitted |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** approved 2026-11-01 by gsd-ui-checker (0 blocks; Dimensions 1, 2, 3, 5 flags applied afterward)
