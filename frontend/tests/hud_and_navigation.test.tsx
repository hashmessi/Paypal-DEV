import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { PromiseProgressionHUD } from '../src/components/domain/PromiseProgressionHUD'
import type { PurchasePromise } from '../src/types/api'

let passedCount = 0
let failedCount = 0

function assert(condition: boolean, testName: string, details?: string) {
  if (condition) {
    passedCount++
    console.log(`  [PASS] ${testName}`)
  } else {
    failedCount++
    console.error(`  [FAIL] ${testName}${details ? ` -> ${details}` : ''}`)
  }
}

function makeMockPromise(overrides: {
  payment?: Partial<PurchasePromise['payment']>
  gate_decision?: PurchasePromise['gate_decision']
  evidence_events?: PurchasePromise['evidence_events']
  receipt_hash?: string
  constraints?: Partial<PurchasePromise['constraints']>
} = {}): PurchasePromise {
  return {
    id: 'prom_test_hud_001',
    ref: 'PL-M3TEST',
    version: 1,
    status: 'approved',
    buyer_instruction: 'Buy 11-inch Apple iPad Pro M4 in Space Black, New condition',
    instruction_source: 'ai',
    constraints: {
      product_type: 'Tablet',
      condition: 'New',
      variant_color: 'Space Black',
      max_total_cents: 120000,
      currency: 'USD',
      deadline_days: 3,
      substitution_allowed: false,
      resolved_deadline_at: '2026-11-05T00:00:00Z',
      ...overrides.constraints,
    },
    product_snapshot: {
      id: 'prod_ipad_m4',
      title: 'Apple iPad Pro 11-inch M4 256GB Space Black',
      brand: 'Apple',
      price_cents: 99900,
      currency: 'USD',
      condition: 'New',
      image_url: 'https://example.com/ipad.png',
      merchant_domain: 'apple-direct.example.com',
      variants: ['Space Black', '256GB'],
      raw_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    },
    merchant_quote: {
      seller_name: 'Apple Store Online',
      seller_domain: 'apple-direct.example.com',
      subtotal_cents: 99900,
      shipping_cents: 0,
      tax_cents: 8242,
      total_cents: 108142,
      currency: 'USD',
      promised_delivery_at: '2026-11-04T18:00:00Z',
      raw_sha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    },
    receipt_hash: overrides.receipt_hash ?? 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123',
    approved_at: '2026-11-02T12:00:00Z',
    payment: {
      order_id: '8XX998877665544',
      authorization_id: '9YY112233445566',
      capture_id: null,
      state: 'authorized',
      amount_cents: 108142,
      currency: 'USD',
      is_simulated: false,
      expiration_time: '2026-11-05T12:00:00Z',
      honor_until: '2026-11-05T12:00:00Z',
      captured_at: null,
      voided_at: null,
      void_reason: null,
      updated_at: '2026-11-02T12:00:00Z',
      ...overrides.payment,
    },
    gate_decision: overrides.gate_decision ?? {
      outcome: 'none',
      findings: [],
      receipt_hash: 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123',
      evaluated_at: '2026-11-02T12:00:00Z',
      rules_version: '2026.11',
    },
    evidence_events: overrides.evidence_events ?? [],
    lifecycle: [],
    created_at: '2026-11-02T11:58:00Z',
    updated_at: '2026-11-02T12:00:00Z',
  }
}

console.log('=== PROMISE PROGRESSION HUD TEST SUITE ===\n')

// -------------------------------------------------------------
// Test Group 1: Canonical 6-Stage Structure Verification
// -------------------------------------------------------------
console.log('Test Group 1: Canonical 6-Stage Structure Verification')

{
  const p = makeMockPromise()
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)

  assert(html.includes('Intent &amp; Constraints') || html.includes('Intent & Constraints'), 'Stage 1: Intent & Constraints rendered')
  assert(html.includes('RFC 8785 Receipt'), 'Stage 2: RFC 8785 Receipt rendered')
  assert(html.includes('PayPal Authorization'), 'Stage 3: PayPal Authorization rendered')
  assert(html.includes('Evidence Ingestion'), 'Stage 4: Evidence Ingestion rendered')
  assert(html.includes('Drift Invariant Gate'), 'Stage 5: Drift Invariant Gate rendered')
  assert(html.includes('Gated Settlement'), 'Stage 6: Gated Settlement rendered')
  assert(html.includes('overflow-x-auto'), 'Responsive container has overflow-x-auto')
  assert(html.includes('sm:grid-cols-6'), 'Responsive desktop layout applies sm:grid-cols-6')
}

// -------------------------------------------------------------
// Test Group 2: Drift Scenario Mapping (Stage 5 Drift + Stage 6 Blocked)
// -------------------------------------------------------------
console.log('\nTest Group 2: Drift Scenario Mapping')

{
  const p = makeMockPromise({
    evidence_events: [
      {
        id: 'evt_001',
        seq: 1,
        source: 'warehouse_pick',
        source_type: 'merchant_system',
        synthetic: false,
        event_type: 'item_picked',
        occurred_at: '2026-11-02T12:10:00Z',
        recorded_at: '2026-11-02T12:10:01Z',
        status_display: 'Item picked',
        payload: { condition: 'Refurbished' },
      },
    ],
    gate_decision: {
      outcome: 'DRIFT',
      receipt_hash: 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123',
      evaluated_at: '2026-11-02T12:10:05Z',
      rules_version: '2026.11',
      findings: [
        {
          code: 'INV-01',
          invariant: 'product',
          severity: 'DRIFT',
          expected: 'New',
          observed: 'Refurbished',
          title: 'Condition Mismatch',
          explanation: 'Buyer approved New condition, warehouse picked Refurbished',
        },
      ],
    },
    payment: {
      state: 'authorized',
    },
  })

  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)

  assert(html.includes('INV-01'), 'Stage 5 surfaces finding code INV-01')
  assert(html.includes('Condition Mismatch'), 'Stage 5 surfaces finding title Condition Mismatch')
  assert(html.includes('CAPTURE BLOCKED'), 'Stage 6 displays CAPTURE BLOCKED on drift')
  assert(html.includes('Invariant Drift Detected'), 'Top summary banner shows Invariant Drift Detected')
  assert(html.includes('1 Ingested'), 'Stage 4 shows 1 Ingested')
}

// -------------------------------------------------------------
// Test Group 3: Match Scenario (Pre-cleared & Ready to Settle)
// -------------------------------------------------------------
console.log('\nTest Group 3: Match Scenario')

{
  const p = makeMockPromise({
    evidence_events: [
      {
        id: 'evt_001',
        seq: 1,
        source: 'warehouse_pick',
        source_type: 'merchant_system',
        synthetic: false,
        event_type: 'item_picked',
        occurred_at: '2026-11-02T12:10:00Z',
        recorded_at: '2026-11-02T12:10:01Z',
        status_display: 'Item picked',
        payload: { condition: 'New' },
      },
    ],
    gate_decision: {
      outcome: 'MATCH',
      receipt_hash: 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123',
      evaluated_at: '2026-11-02T12:10:05Z',
      rules_version: '2026.11',
      findings: [],
    },
    payment: {
      state: 'authorized',
    },
  })

  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)

  assert(html.includes('MATCH'), 'Stage 5 displays MATCH badge')
  assert(html.includes('All 8 invariants verified'), 'Stage 5 confirms All 8 invariants verified')
  assert(html.includes('READY TO CAPTURE'), 'Stage 6 displays READY TO CAPTURE')
  assert(html.includes('Invariants Verified'), 'Top summary banner shows Invariants Verified')
}

// -------------------------------------------------------------
// Test Group 4: Captured Settlement State
// -------------------------------------------------------------
console.log('\nTest Group 4: Captured Settlement State')

{
  const p = makeMockPromise({
    evidence_events: [
      {
        id: 'evt_001',
        seq: 1,
        source: 'warehouse_pick',
        source_type: 'merchant_system',
        synthetic: false,
        event_type: 'item_picked',
        occurred_at: '2026-11-02T12:10:00Z',
        recorded_at: '2026-11-02T12:10:01Z',
        status_display: 'Item picked',
        payload: { condition: 'New' },
      },
    ],
    gate_decision: {
      outcome: 'MATCH',
      receipt_hash: 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123',
      evaluated_at: '2026-11-02T12:10:05Z',
      rules_version: '2026.11',
      findings: [],
    },
    payment: {
      state: 'captured',
      capture_id: 'CAP-LIVE-987654321',
      captured_at: '2026-11-02T12:15:00Z',
    },
  })

  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)

  assert(html.includes('CAPTURED'), 'Stage 6 displays CAPTURED')
  assert(html.includes('Funds settled to merchant'), 'Stage 6 indicates funds settled to merchant')
  assert(html.includes('Settled to Merchant'), 'Top summary banner indicates Settled to Merchant')
}

// -------------------------------------------------------------
// Test Group 5: Voided Settlement State
// -------------------------------------------------------------
console.log('\nTest Group 5: Voided Settlement State')

{
  const p = makeMockPromise({
    payment: {
      state: 'voided',
      void_reason: 'Operator rejected mismatch',
      voided_at: '2026-11-02T12:20:00Z',
    },
  })

  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)

  assert(html.includes('VOIDED'), 'Stage 6 displays VOIDED')
  assert(html.includes('Operator rejected mismatch'), 'Stage 6 displays operator void reason')
}

console.log(`\n=================================================`)
console.log(`Results: ${passedCount} PASSED, ${failedCount} FAILED`)
console.log(`=================================================`)

if (failedCount > 0) {
  process.exit(1)
}
