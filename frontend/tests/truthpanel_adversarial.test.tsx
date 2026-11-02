import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { TruthPanel } from '../src/components/domain/TruthPanel'
import type { PurchasePromise, PaymentState, GateOutcome } from '../src/types/api'

// Minimal test harness with assertions
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
  counterfactual?: Partial<PurchasePromise['counterfactual']>
  gate_decision?: PurchasePromise['gate_decision']
} = {}): PurchasePromise {
  return {
    id: 'prom_adv_test_001',
    ref: 'ORD-TEST-ADV',
    buyer_instruction: 'Test instruction',
    instruction_source: 'fallback',
    constraints: [],
    product_snapshot: {
      merchant_id: 'merch_01',
      title: 'Sony WH-1000XM5',
      sku: 'SONY-XM5-BLK',
      condition: 'NEW',
      price_cents: 8999,
      currency: 'USD',
      inventory_status: 'IN_STOCK',
      source_url: 'https://example.com',
      captured_at: '2026-11-02T12:00:00Z',
    },
    merchant_quote: {
      subtotal_cents: 8999,
      shipping_cents: 0,
      tax_cents: 0,
      total_cents: 8999,
      currency: 'USD',
      estimated_delivery_days: 2,
    },
    receipt_hash: 'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    approved_at: '2026-11-02T12:01:00Z',
    payment: {
      order_id: 'ORDER-REAL-12345',
      authorization_id: 'AUTH-REAL-67890',
      capture_id: null,
      state: 'authorized',
      amount_cents: 8999,
      currency: 'USD',
      expiration_time: '2026-11-05T12:00:00Z',
      honor_until: '2026-11-05T12:00:00Z',
      captured_at: null,
      voided_at: null,
      void_reason: null,
      is_simulated: false,
      updated_at: '2026-11-02T12:01:00Z',
      ...overrides.payment,
    },
    gate_decision: overrides.gate_decision ?? {
      outcome: 'none',
      evaluated_at: '2026-11-02T12:01:00Z',
      findings: [],
      reason: 'Awaiting evidence',
    },
    evidence_events: [],
    counterfactual: 'counterfactual' in overrides
      ? (overrides.counterfactual as PurchasePromise['counterfactual'])
      : {
          baseline_flow: 'direct_capture',
          simulated: false,
        },
    lifecycle: [],
    created_at: '2026-11-02T12:00:00Z',
    updated_at: '2026-11-02T12:01:00Z',
  }
}

console.log('=== TRUTHPANEL ADVERSARIAL STRESS TEST SUITE ===\n')

// -------------------------------------------------------------
// Test Group 1: Null/Undefined ID Edge Cases & Mock Leaks
// -------------------------------------------------------------
console.log('Test Group 1: Null/Undefined IDs & Fake Mock String Leaks')

{
  // All IDs null, state created
  const p = makeMockPromise({
    payment: {
      order_id: null,
      authorization_id: null,
      capture_id: null,
      state: 'created',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(!html.includes('3KX8291048194'), 'No hardcoded fake Order ID 3KX8291048194')
  assert(!html.includes('9K3184920194'), 'No hardcoded fake Auth ID 9K3184920194')
  assert(!html.includes('3KX'), 'No synthetic 3KX prefix in IDs')
  assert(!html.includes('9K3'), 'No synthetic 9K3 prefix in IDs')
  assert(html.includes('Awaiting order'), 'Null order_id in state created renders "Awaiting order"')
  assert(html.includes('N/A'), 'Null authorization_id renders "N/A"')
  assert(html.includes('Not submitted'), 'Null capture_id in state created renders "Not submitted"')
}

{
  // All IDs undefined, state authorized
  const p = makeMockPromise({
    payment: {
      order_id: undefined as unknown as null,
      authorization_id: undefined as unknown as null,
      capture_id: undefined as unknown as null,
      state: 'authorized',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(!html.includes('undefined'), 'Rendered HTML does not leak verbatim "undefined"')
  assert(!html.includes('null'), 'Rendered HTML does not leak verbatim "null"')
  assert(html.includes('Authorized · not captured'), 'Renders Authorized state pill')
  assert(html.includes('Not submitted'), 'Capture ID displays "Not submitted"')
}

{
  // Empty strings in IDs
  const p = makeMockPromise({
    payment: {
      order_id: '',
      authorization_id: '',
      capture_id: '',
      state: 'authorized',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(!html.includes('3KX'), 'Empty strings do not trigger fake ID fallbacks')
  assert(html.includes('N/A'), 'Empty string order_id/auth_id display N/A')
}

{
  // Drift gate decision blocks capture display
  const p = makeMockPromise({
    payment: {
      capture_id: null,
      state: 'authorized',
    },
    gate_decision: {
      outcome: 'DRIFT',
      evaluated_at: '2026-11-02T12:05:00Z',
      findings: [{ code: 'SKU_MISMATCH', title: 'Wrong SKU delivered', severity: 'CRITICAL' }],
      reason: 'Fulfillment item did not match promise',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Blocked by drift gate'), 'DRIFT outcome displays "Blocked by drift gate"')
  assert(html.includes('text-[var(--color-bad)]'), 'Blocked text has error tone styling')
}

// -------------------------------------------------------------
// Test Group 2: Voided State Handling
// -------------------------------------------------------------
console.log('\nTest Group 2: Voided State Handling')

{
  // Full voided metadata
  const p = makeMockPromise({
    payment: {
      state: 'voided',
      capture_id: null,
      voided_at: '2026-11-02T14:30:00Z',
      void_reason: 'Drift gate rejected condition: Used item supplied',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Released hold'), 'Voided state header displays "Released hold"')
  assert(html.includes('Authorization voided'), 'Voided banner is visible')
  assert(html.includes('2026-11-02T14:30:00Z'), 'Void timestamp is rendered verbatim')
  assert(html.includes('Drift gate rejected condition: Used item supplied'), 'Void reason is rendered verbatim')
  assert(html.includes('Voided'), 'Capture ID displays "Voided"')
}

{
  // Voided state without timestamp or reason (edge case)
  const p = makeMockPromise({
    payment: {
      state: 'voided',
      capture_id: null,
      voided_at: null,
      void_reason: null,
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Released hold'), 'Voided state without details still displays "Released hold"')
  assert(html.includes('Authorization voided'), 'Void banner renders without crashing')
  assert(!html.includes('Reason:'), 'No empty Reason label rendered when void_reason is null')
}

{
  // Captured state
  const p = makeMockPromise({
    payment: {
      state: 'captured',
      capture_id: 'CAP-9988776655',
      captured_at: '2026-11-02T13:00:00Z',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Captured settlement'), 'Captured state displays "Captured settlement"')
  assert(html.includes('CAP-9988776655'), 'Capture ID rendered via HashChip')
  assert(!html.includes('Authorization voided'), 'No void banner on captured promise')
}

// -------------------------------------------------------------
// Test Group 3: Simulated vs Live Badging & Tones
// -------------------------------------------------------------
console.log('\nTest Group 3: Simulated vs Live Badging Tones & Text')

{
  // Live Sandbox: payment.is_simulated === false
  const p = makeMockPromise({
    payment: { is_simulated: false },
    counterfactual: { simulated: false },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('PayPal Sandbox · live API'), 'Live mode renders "PayPal Sandbox · live API"')
  assert(html.includes('Real Orders v2 &amp; Payments v2 Sandbox'), 'Live subtitle rendered')
  assert(html.includes('bg-[var(--color-ok-soft)]'), 'Live badge uses ok tone background')
  assert(html.includes('text-[var(--color-ok)]'), 'Live badge uses ok tone text')
  assert(html.includes('bg-[var(--color-ok)]'), 'Live badge dot uses ok green')
  assert(!html.includes('Simulated gateway'), 'Live mode does NOT contain "Simulated gateway"')
}

{
  // Simulated Gateway: payment.is_simulated === true
  const p = makeMockPromise({
    payment: { is_simulated: true },
    counterfactual: { simulated: true },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Simulated gateway'), 'Simulated mode renders "Simulated gateway"')
  assert(html.includes('Simulated Orders v2 gateway'), 'Simulated subtitle rendered')
  assert(html.includes('bg-[var(--color-info-soft)]'), 'Simulated badge uses info tone background')
  assert(html.includes('text-[var(--color-info)]'), 'Simulated badge uses info tone text')
  assert(html.includes('bg-[var(--color-info)]'), 'Simulated badge dot uses info blue')
  assert(!html.includes('PayPal Sandbox · live API'), 'Simulated mode does NOT contain live badge text')
}

{
  // Fallback to counterfactual: payment.is_simulated === undefined, counterfactual.simulated === false
  const p = makeMockPromise({
    payment: { is_simulated: undefined as unknown as boolean },
    counterfactual: { simulated: false },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('PayPal Sandbox · live API'), 'Falls back to counterfactual.simulated === false')
  assert(html.includes('bg-[var(--color-ok-soft)]'), 'Fallback live badge tone is ok')
}

{
  // Fallback when both are missing: safe default to simulated
  const p = makeMockPromise({
    payment: { is_simulated: undefined as unknown as boolean },
    counterfactual: undefined,
  })
  const html = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={p} />)
  assert(html.includes('Simulated gateway'), 'Default when missing is Simulated gateway')
  assert(html.includes('bg-[var(--color-info-soft)]'), 'Default badge tone is info')
}

// -------------------------------------------------------------
// Test Group 4: Visual and Programmatic Robustness
// -------------------------------------------------------------
console.log('\nTest Group 4: Visual and Programmatic Robustness')

{
  // Children slot rendering
  const p = makeMockPromise()
  const html = ReactDOMServer.renderToStaticMarkup(
    <TruthPanel promise={p} className="custom-test-class">
      <div id="test-child-slot">Audit action button</div>
    </TruthPanel>
  )
  assert(html.includes('test-child-slot'), 'Children slot rendered within TruthPanel')
  assert(html.includes('Audit action button'), 'Children content rendered properly')
  assert(html.includes('custom-test-class'), 'Custom className propagated')
}

{
  // Extreme currency and minor unit testing
  const pZero = makeMockPromise({ payment: { amount_cents: 0, currency: 'USD' } })
  const htmlZero = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={pZero} />)
  assert(htmlZero.includes('$0.00'), 'Zero amount formatted as $0.00')

  const pLarge = makeMockPromise({ payment: { amount_cents: 125000000, currency: 'USD' } })
  const htmlLarge = ReactDOMServer.renderToStaticMarkup(<TruthPanel promise={pLarge} />)
  assert(htmlLarge.includes('$1,250,000.00'), 'Large amount formatted with commas: $1,250,000.00')
}

console.log(`\n=================================================`)
console.log(`Results: ${passedCount} PASSED, ${failedCount} FAILED`)
console.log(`=================================================`)

if (failedCount > 0) {
  process.exit(1)
}
