# PromiseLoop — UX Research Plan & Synthesis (pre-build)

> **Evidence status: HYPOTHESES, not findings.** No participants have been interviewed. Everything in
> "Synthesis" is derived from `paypal.dev.product.md`, `.planning/REQUIREMENTS.md` and the three reference
> screens. It exists to set UI priorities now and to be *tested* in the usability sessions below.
> Do not quote any of it in the README or Devpost as user evidence.

Feeds: `.planning/ui/UI-SPEC.md` (contract) and `frontend/UI.md` (build guide).

---

## 1. Research objectives

| # | Question | Decides |
|---|----------|---------|
| Q1 | Can a first-time evaluator tell **authorized** from **paid** on every screen? | Status pill vocabulary, "Not an escrow" copy |
| Q2 | After a block, can they say **why** capture was held, **what was expected vs observed**, and **what unblocks it** without reading docs? | Drift review layout, finding copy |
| Q3 | Do they trust the Promise Receipt as an approval artifact (hash, frozen constraints) or read it as decoration? | Receipt hierarchy, hash display |
| Q4 | Can they run the full 8-act scenario unaided from the live URL in under 5 minutes? | Judge Start page, Scenario Console, cold-start notice |
| Q5 | Do they understand which evidence is SYNTHETIC and what the product does **not** prove? | Badges, proves / does-not-prove table |

## 2. Users and jobs-to-be-done

| User | Role in the product | Job (JTBD) | Success looks like |
|------|--------------------|------------|--------------------|
| **Merchant / platform risk operator** (primary persona) | Watches the Control Tower, resolves drift | "When an AI agent's order is fulfilled, I need proof the exact item, price and conditions were respected **before** I settle, so I never capture a contract violation." | Resolves a blocked case (correct or void) in under 60 s with a reason on record |
| **Shopper (buyer approving an agent purchase)** | Approves one exact receipt | "When my agent buys for me, I need to approve the exact item and limits once, and know my money is only taken if they are met." | Approves a hash they understood; never sees a surprise total |
| **Hackathon judge / evaluator** (decisive near-term user) | Runs the demo on a fresh browser, no keys | "Show me the technical core working end-to-end on real PayPal Sandbox calls, quickly, and tell me honestly what is simulated." | Completes the 8 acts, sees a real capture, can name the limits |
| Security / audit reviewer (secondary) | Reads Replay | "Reconstruct what happened and detect tampering." | Verifies integrity, finds the divergence step in one glance |

## 3. Method (sized to an 11-day solo build)

| Method | Why this one | n | When | Cost |
|--------|--------------|---|------|------|
| **Moderated usability walkthrough** on the live Render URL | Only method that fits the deadline and tests Q1–Q5 on the real flow | 5 (peers / developers / PMs as judge proxies) | **Nov 8–9**, after Phase 3 ships, before Phase 4 polish | ~25 min each |
| 5-second receipt test | Q1/Q3: screenshot of the Receipt page, "what is the state of this payment?" | 5 (same sessions) | Same | 2 min |
| Heuristic self-review against UI-SPEC checklist | Free; catches contract drift | 1 | Each phase end (`/gsd-ui-review`) | 20 min |

Not planned (explicit): surveys, A/B tests, card sorting, diary studies. Sample too small or unneeded for a 5-route app.

## 4. Session guide (25 min)

| Block | Min | Script |
|-------|-----|--------|
| Warm-up | 3 | "We're testing the product, not you. Think aloud. I can't answer how-do-I questions until the end." |
| Context | 4 | "Have you handled card authorizations, holds or chargebacks? Describe the last time an order arrived wrong." Probe: who found out, how long, what did it cost. |
| Task 1 — run it | 6 | "You've been sent this link. Show me what it does and complete one purchase." (Do **not** mention Scenario Console.) Observe: time-to-first-action, hesitation at the PayPal popup, cold-start reaction. |
| Task 2 — the block | 6 | Trigger refurbished. Ask: "Is the buyer's money taken? Why or why not? What would you do next?" Then: "Fix it." |
| Task 3 — proof | 4 | Open Replay. "Which step went wrong? How would you know someone edited history?" Click **Verify integrity**. |
| Wrap-up | 2 | "What would you not trust here? What's missing?" |

## 5. Success criteria (pass / fail, recorded per participant)

| ID | Criterion | Pass bar (of 5) |
|----|-----------|-----------------|
| S1 | Completes run → authorize → blocked → corrected → captured unaided | ≥ 4 |
| S2 | Total time for S1 | median ≤ 5 min |
| S3 | Says "authorized" ≠ "paid" in own words after Act 4 | 5 / 5 |
| S4 | Names expected vs observed (New vs Refurbished) without prompting | ≥ 4 |
| S5 | Identifies the divergence step in Replay within 15 s | ≥ 4 |
| S6 | Correctly states that the evidence is simulated | ≥ 4 |
| S7 | Any participant clicks an enabled control believing it moves money when it does not | 0 |

Any failure of S3, S6 or S7 is a **P0 copy/IA fix** before submission.

## 6. Journey map (the 8 demo acts)

| Act | Screen | User goal | Likely doubt / risk | Required UI response |
|-----|--------|-----------|---------------------|----------------------|
| 1 Instruction | Shopper Agent | Say what I want | "Did the AI understand me?" | Editable typed constraints, labeled **AI extracted** or **Fallback parser** |
| 2 Discovery | Shopper Agent | Pick the exact item | "Is this real? Is the price final?" | Real candidates; condition `UNVERIFIED` shown, never "New"; quote labeled "Sandbox stand-in for `<domain>`" |
| 3 Receipt | Shopper Agent → Receipt | Approve once | "What exactly am I agreeing to?" | Frozen constraints list + hash; button names the hash |
| 4 Authorize | Shopper Agent | Hold the funds | "Was I charged?" | **AUTHORIZED · NOT CAPTURED**, "Not an escrow service" |
| 5 Mismatch | Control Tower / Drift review | Understand the block | "Is this a bug?" | Expected vs observed side by side, invariant code, "Capture held" |
| 6 Correction | Drift review | Fix and retry | "Will it capture automatically?" | Scenario action labeled SYNTHETIC; state "re-evaluating" then result |
| 7 Verified | Receipt | See money move once | "Did it capture twice?" | **CAPTURED**, one capture ID, webhook row |
| 8 Replay | Replay | Prove it | "Can I trust this log?" | 10 steps on one screen, divergence highlighted, **Verify integrity** |

## 7. Synthesis hypotheses → design decisions (to validate in sessions)

Impact × effort, highest first.

| # | Hypothesis | Impact | Effort | Design response (where) |
|---|-----------|--------|--------|-------------------------|
| H1 | Evaluators conflate "Authorized" with "Paid" | High | Low | Two columns everywhere (Authorization vs Gate); amber for authorized-not-captured; fixed caption (UI-SPEC §Status) |
| H2 | A bare "Capture blocked" feels like an error, not a feature | High | Low | Frame as a result: finding title + expected/observed + "what unblocks it" |
| H3 | Cold start (~1 min on Render free) reads as a broken product | High | Low | Persistent wake-up banner with progress, retry with backoff, never a blank screen |
| H4 | Judges skip the README | High | Medium | Judge Start page `/` has the 3-step guide and one primary action |
| H5 | Hashes are ignored unless they do something | Medium | Low | "Verify integrity" and approve-hash button give the hash a verb |
| H6 | Synthetic controls look like real merchant actions | High | Low | Console panel permanently labeled SYNTHETIC; amber outline |
| H7 | Operators need to see time-to-expiry to prioritize | Medium | Low | Countdown column + sort default |

## 8. Synthesis template (fill after sessions)

```
Participant: P# · role · date
S1–S7: pass/fail + note
Quotes (verbatim, ≤ 2): ...
Confusions (screen · moment · what they said): ...
Fix (UI-SPEC section · severity P0/P1/P2): ...
```

Roll-up rule: a problem seen by ≥ 2 of 5 participants becomes a fix; seen by 1 stays a note.
