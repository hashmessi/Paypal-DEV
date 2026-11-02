-- PromiseLoop Database Schema (PostgreSQL DDL)
-- Hard Gate: Append-only ledger enforced via trigger

CREATE TABLE IF NOT EXISTS purchases (
    id VARCHAR(36) PRIMARY KEY,
    ref VARCHAR(32) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    buyer_instruction TEXT NOT NULL,
    receipt_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchases_ref ON purchases(ref);

CREATE TABLE IF NOT EXISTS payment_authorizations (
    id VARCHAR(36) PRIMARY KEY,
    purchase_id VARCHAR(36) NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    order_id VARCHAR(64),
    authorization_id VARCHAR(64) UNIQUE,
    state VARCHAR(32) NOT NULL DEFAULT 'created',
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    expiration_time TIMESTAMP WITH TIME ZONE,
    honor_until TIMESTAMP WITH TIME ZONE,
    capture_id VARCHAR(64),
    captured_at TIMESTAMP WITH TIME ZONE,
    voided_at TIMESTAMP WITH TIME ZONE,
    void_reason VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pay_auth_order_id ON payment_authorizations(order_id);
CREATE INDEX IF NOT EXISTS idx_pay_auth_auth_id ON payment_authorizations(authorization_id);

CREATE TABLE IF NOT EXISTS financial_actions (
    id VARCHAR(36) PRIMARY KEY,
    authorization_id VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    response_payload TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_auth_action UNIQUE (authorization_id, action)
);

CREATE TABLE IF NOT EXISTS decision_events (
    id VARCHAR(36) PRIMARY KEY,
    seq INTEGER NOT NULL,
    purchase_id VARCHAR(36) NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL,
    payload TEXT NOT NULL,
    prev_hash VARCHAR(64) NOT NULL,
    event_hash VARCHAR(64) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_purchase_event_seq UNIQUE (purchase_id, seq)
);

CREATE INDEX IF NOT EXISTS idx_decision_events_purchase_id ON decision_events(purchase_id);

CREATE TABLE IF NOT EXISTS webhook_events (
    event_id VARCHAR(128) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NOT NULL,
    raw_body TEXT NOT NULL,
    headers TEXT NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_resource_id ON webhook_events(resource_id);

-- Append-only trigger for decision_events (blocks UPDATE / DELETE)
CREATE OR REPLACE FUNCTION prevent_decision_events_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'decision_events is an immutable append-only ledger. UPDATE and DELETE operations are prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_decision_events_immutable ON decision_events;
CREATE TRIGGER trg_decision_events_immutable
BEFORE UPDATE OR DELETE ON decision_events
FOR EACH ROW
EXECUTE FUNCTION prevent_decision_events_mutation();


-- Promise Receipts: Versioned, sealed promise receipts
CREATE TABLE IF NOT EXISTS promise_receipts (
    id VARCHAR(36) PRIMARY KEY,
    purchase_id VARCHAR(36) NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    receipt_hash VARCHAR(64) NOT NULL,
    canonical_payload TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    product_snapshot_json TEXT NOT NULL,
    merchant_quote_json TEXT NOT NULL,
    capture_conditions_json TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_purchase_receipt_version UNIQUE (purchase_id, version)
);

CREATE INDEX IF NOT EXISTS idx_promise_receipts_hash ON promise_receipts(receipt_hash);
CREATE INDEX IF NOT EXISTS idx_promise_receipts_purchase ON promise_receipts(purchase_id);

-- Extraction Cache: Caches natural language parse results
CREATE TABLE IF NOT EXISTS extraction_cache (
    instruction_hash VARCHAR(64) PRIMARY KEY,
    instruction_text TEXT NOT NULL,
    constraints_json TEXT NOT NULL,
    source VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Immutability rule for approved receipts:
-- Once status is 'approved', it can transition to 'stale' or 'superseded', but its core financial terms
-- (receipt_hash, total_cents, canonical_payload, constraints, quote) cannot be altered.
CREATE OR REPLACE FUNCTION prevent_approved_receipt_tampering()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'approved' AND (
        NEW.receipt_hash <> OLD.receipt_hash OR
        NEW.total_cents <> OLD.total_cents OR
        NEW.canonical_payload <> OLD.canonical_payload
    ) THEN
        RAISE EXCEPTION 'Approved receipts are immutable. Cannot alter receipt_hash, total_cents, or payload once approved.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_promise_receipts_immutable ON promise_receipts;
CREATE TRIGGER trg_promise_receipts_immutable
BEFORE UPDATE ON promise_receipts
FOR EACH ROW
EXECUTE FUNCTION prevent_approved_receipt_tampering();

-- Fulfillment Evidence: Typed fulfillment evidence events (FULF-01)
CREATE TABLE IF NOT EXISTS fulfillment_evidence (
    id VARCHAR(36) PRIMARY KEY,
    purchase_id VARCHAR(36) NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    seq INTEGER NOT NULL,
    source VARCHAR(64) NOT NULL,
    external_event_id VARCHAR(128) NOT NULL,
    trust_level VARCHAR(32) NOT NULL DEFAULT 'CARRIER_TELEMETRY',
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    carrier_status VARCHAR(32),
    sku VARCHAR(64),
    condition VARCHAR(32),
    color VARCHAR(32),
    eta TIMESTAMP WITH TIME ZONE,
    raw_payload TEXT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_evidence_dedup UNIQUE (purchase_id, source, external_event_id)
);

CREATE INDEX IF NOT EXISTS idx_fulfillment_evidence_purchase ON fulfillment_evidence(purchase_id);

-- Gate Evaluations: Deterministic invariant evaluations (DRIFT-01)
CREATE TABLE IF NOT EXISTS gate_evaluations (
    id VARCHAR(36) PRIMARY KEY,
    purchase_id VARCHAR(36) NOT NULL REFERENCES purchases(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    outcome VARCHAR(32) NOT NULL,
    status_pill VARCHAR(64) NOT NULL,
    findings_json TEXT NOT NULL,
    explanation TEXT,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gate_evaluations_purchase ON gate_evaluations(purchase_id);
