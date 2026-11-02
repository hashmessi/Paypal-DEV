# Phase 01: Money Spine on a Public URL — Context & Constraints

**Phase:** 01-money-spine-on-a-public-url
**Status:** In Progress
**Target Date:** Nov 2, 2026 (Hard Gate)
**Requirements Covered:** PAY-01, PAY-03, PAY-04, PAY-05, PAY-06, LEDG-01, DEPLOY-01

---

## 1. Goal & Boundaries

Build and verify the financial core ("Money Spine") of PromiseLoop:
1. Create PayPal Orders v2 with `intent=AUTHORIZE`
2. Payer approves hold via JS SDK / Sandbox credentials
3. Server authorizes and stores Order ID, Authorization ID, amount, and `expiration_time`
4. Idempotent capture with `final_capture: true` and deterministic `PayPal-Request-Id`
5. Operator void with required reason code; terminal state enforcement (a voided authorization can never be captured)
6. Raw-body PayPal webhook verification, deduplication by `event_id`, and ledger recording
7. Append-only, hash-chained ledger (`decision_events`) with tamper-detection verification (`verify_chain`)
8. Render Blueprint deployment specification (`render.yaml`) for FastAPI + Postgres + React static site

---

## 2. Invariant & Architecture Decisions

- **Architecture:** FastAPI modular monolith, SQLAlchemy 2.0 async/sync engine, PostgreSQL (with SQLite compatibility for fast offline pytest suite).
- **Idempotency:** `financial_actions` table with `UNIQUE(authorization_id, action)` and deterministic persisted `PayPal-Request-Id` = `uuid5(NAMESPACE, f"{authorization_id}:{action}")`.
- **State Machine:** Strictly enforces legal transitions:
  `created → approved → authorized → capturing → captured / capture_pending / voided / expired / failed`.
- **Ledger:** Hash-chained where `event_hash = sha256(prev_hash + seq + event_type + canonical_json(payload) + recorded_at)`. Genesis block uses `0000000000000000000000000000000000000000000000000000000000000000`.
- **Clock:** Injected `Clock` protocol (`SystemClock`, `FixedClock`, `DemoOffsetClock`) to prevent expired calendar dates during judging.
- **Webhooks:** Captured response is authoritative for money truth; webhooks provide postback confirmation and ledger record. Webhooks NEVER trigger capture.

