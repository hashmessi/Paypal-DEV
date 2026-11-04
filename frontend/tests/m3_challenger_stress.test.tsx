import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { MemoryRouter } from 'react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PromiseProgressionHUD } from '../src/components/domain/PromiseProgressionHUD'
import { StartPage } from '../src/pages/Start'
import { Sidebar } from '../src/layout/Sidebar'
import type { PurchasePromise } from '../src/types/api'

let passed = 0
let failed = 0

function assert(cond: boolean, name: string, detail?: string) {
  if (cond) {
    passed++
    console.log(`  [PASS] ${name}`)
  } else {
    failed++
    console.error(`  [FAIL] ${name} ${detail ? `-> ${detail}` : ''}`)
  }
}

function makePromise(overrides: {
  payment?: Partial<PurchasePromise['payment']>
  gate_decision?: PurchasePromise['gate_decision']
  evidence_events?: PurchasePromise['evidence_events']
  receipt_hash?: string
  constraints?: Partial<PurchasePromise['constraints']>
} = {}): PurchasePromise {
  return {
    id: 'prom_stress_test_01',
    ref: 'PL-CHALLENGER',
    version: 1,
    status: 'approved',
    buyer_instruction: 'Purchase certified Apple iPad M4 11-inch Space Black',
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
    receipt_hash: overrides.receipt_hash !== undefined
      ? overrides.receipt_hash
      : 'sha256:9a8b7c6d5e4f3210fedcba98765432109a8b7c6d5e4f3210fedcba9876543210',
    approved_at: '2026-11-02T12:00:00Z',
    payment: {
      order_id: 'ORDER-PAYPAL-12345',
      authorization_id: 'AUTH-PAYPAL-67890',
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
      receipt_hash: 'sha256:9a8b7c6d5e4f3210fedcba98765432109a8b7c6d5e4f3210fedcba9876543210',
      evaluated_at: '2026-11-02T12:00:00Z',
      rules_version: '2026.11',
    },
    evidence_events: overrides.evidence_events ?? [],
    lifecycle: [],
    created_at: '2026-11-02T11:58:00Z',
    updated_at: '2026-11-02T12:00:00Z',
  }
}

console.log('=== EMPIRICAL CHALLENGER: M3 ADVERSARIAL STRESS SUITE ===\n')

// =========================================================================
// SECTION 1: Stage 5 Drift Invariant Gate State Transitions
// =========================================================================
console.log('--- SECTION 1: Stage 5 Drift Invariant Gate Transitions ---')

// 1.1: DRIFT outcome with specific finding code and title
{
  const p = makePromise({
    gate_decision: {
      outcome: 'DRIFT',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [
        {
          code: 'INV-02',
          invariant: 'spending',
          severity: 'DRIFT',
          expected: 108142,
          observed: 119900,
          title: 'Price Exceeded Cap',
          explanation: 'Captured amount exceeds buyer authorization cap',
        },
      ],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('INV-02'), '1.1: Stage 5 displays finding code INV-02')
  assert(html.includes('Price Exceeded Cap'), '1.1: Stage 5 displays finding title')
  assert(html.includes('Invariant Drift Detected'), '1.1: Header banner alerts Invariant Drift Detected')
  assert(html.includes('border-[var(--color-bad-line)]'), '1.1: Stage 5 uses bad tone border styling')
}

// 1.2: DRIFT outcome without findings (fallback handling)
{
  const p = makePromise({
    gate_decision: {
      outcome: 'DRIFT',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('DRIFT'), '1.2: Stage 5 displays fallback badge DRIFT when no finding code')
  assert(html.includes('Condition Mismatch detected'), '1.2: Stage 5 displays fallback detail when no findings')
}

// 1.3: MATCH outcome
{
  const p = makePromise({
    gate_decision: {
      outcome: 'MATCH',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('MATCH'), '1.3: Stage 5 displays MATCH badge')
  assert(html.includes('All 8 invariants verified'), '1.3: Stage 5 displays verified invariants detail')
  assert(html.includes('Invariants Verified'), '1.3: Header banner confirms Invariants Verified')
  assert(html.includes('border-[var(--color-ok-line)]'), '1.3: Stage 5 uses ok tone border styling')
}

// 1.4: HOLD outcome with operator finding
{
  const p = makePromise({
    gate_decision: {
      outcome: 'HOLD',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [
        {
          code: 'HOLD-01',
          invariant: 'execution',
          severity: 'HOLD',
          expected: 'clean',
          observed: 'manual_hold',
          title: 'Manual Review Requested',
          explanation: 'Operator flagged shipment for serial validation',
        },
      ],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('HOLD'), '1.4: Stage 5 displays HOLD badge')
  assert(html.includes('Manual Review Requested'), '1.4: Stage 5 displays custom operator finding title')
  assert(html.includes('border-[var(--color-warn-line)]'), '1.4: Stage 5 uses warn tone border styling')
}

// 1.5: HOLD outcome without finding title (fallback handling)
{
  const p = makePromise({
    gate_decision: {
      outcome: 'HOLD',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('HOLD'), '1.5: Stage 5 displays HOLD badge')
  assert(html.includes('Operator hold active'), '1.5: Stage 5 displays fallback detail Operator hold active')
}

// 1.6: None / Pending outcome with 0 evidence events
{
  const p = makePromise({
    gate_decision: {
      outcome: 'none',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
    evidence_events: [],
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('Pending'), '1.6: Stage 5 displays Pending badge')
  assert(html.includes('Awaiting telemetry'), '1.6: Stage 5 displays Awaiting telemetry')
}

// 1.7: None outcome with evidence events (Evaluating state)
{
  const p = makePromise({
    gate_decision: {
      outcome: 'none',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
    evidence_events: [
      {
        id: 'evt_1',
        seq: 1,
        source: 'warehouse_pick',
        source_type: 'merchant_system',
        synthetic: false,
        event_type: 'item_picked',
        occurred_at: '2026-11-02T14:05:00Z',
        recorded_at: '2026-11-02T14:05:01Z',
        status_display: 'Item picked',
        payload: { serial: '12345' },
      },
    ],
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('Evaluating'), '1.7: Stage 5 displays Evaluating badge when telemetry received')
  assert(html.includes('Evaluating invariants'), '1.7: Stage 5 displays Evaluating invariants')
}

// =========================================================================
// SECTION 2: Stage 6 Gated Settlement State Transitions
// =========================================================================
console.log('\n--- SECTION 2: Stage 6 Gated Settlement Transitions ---')

// 2.1: CAPTURED with captured_at timestamp
{
  const p = makePromise({
    payment: {
      state: 'captured',
      captured_at: '2026-11-02T14:30:00Z',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('CAPTURED'), '2.1: Stage 6 displays CAPTURED badge')
  assert(html.includes('Funds settled to merchant'), '2.1: Stage 6 displays Funds settled to merchant')
  assert(html.includes('Settled to Merchant'), '2.1: Header banner confirms Settled to Merchant')
}

// 2.2: CAPTURED without captured_at timestamp (live Orders v2 fallback)
{
  const p = makePromise({
    payment: {
      state: 'captured',
      captured_at: null,
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('CAPTURED'), '2.2: Stage 6 displays CAPTURED badge')
  assert(html.includes('Captured via live Orders v2'), '2.2: Stage 6 displays Captured via live Orders v2')
}

// 2.3: VOIDED with void_reason
{
  const p = makePromise({
    payment: {
      state: 'voided',
      void_reason: 'Buyer canceled order due to condition drift',
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('VOIDED'), '2.3: Stage 6 displays VOIDED badge')
  assert(html.includes('Buyer canceled order due to condition drift'), '2.3: Stage 6 displays specific void reason')
}

// 2.4: VOIDED without void_reason (fallback detail)
{
  const p = makePromise({
    payment: {
      state: 'voided',
      void_reason: null,
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('VOIDED'), '2.4: Stage 6 displays VOIDED badge')
  assert(html.includes('Authorization released'), '2.4: Stage 6 displays fallback detail Authorization released')
}

// 2.5: CAPTURE BLOCKED on authorized + DRIFT
{
  const p = makePromise({
    payment: { state: 'authorized' },
    gate_decision: {
      outcome: 'DRIFT',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [{ code: 'INV-01', invariant: 'product', severity: 'DRIFT', expected: 'New', observed: 'Used', title: 'Used Item', explanation: 'Mismatch' }],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('CAPTURE BLOCKED'), '2.5: Stage 6 displays CAPTURE BLOCKED badge on drift')
  assert(html.includes('Hold locked · settlement blocked'), '2.5: Stage 6 indicates hold locked settlement blocked')
  assert(html.includes('border-[var(--color-bad-line)]'), '2.5: Stage 6 uses bad tone border styling on drift')
}

// 2.6: READY TO CAPTURE on authorized + MATCH
{
  const p = makePromise({
    payment: { state: 'authorized' },
    gate_decision: {
      outcome: 'MATCH',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('READY TO CAPTURE'), '2.6: Stage 6 displays READY TO CAPTURE badge on match')
  assert(html.includes('Pre-cleared · capture permitted'), '2.6: Stage 6 indicates pre-cleared capture permitted')
  assert(html.includes('border-[var(--color-ok-line)]'), '2.6: Stage 6 uses ok tone border styling')
}

// 2.7: SETTLEMENT HOLD on authorized + HOLD
{
  const p = makePromise({
    payment: { state: 'authorized' },
    gate_decision: {
      outcome: 'HOLD',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('SETTLEMENT HOLD'), '2.7: Stage 6 displays SETTLEMENT HOLD badge')
  assert(html.includes('Held pending human review'), '2.7: Stage 6 indicates Held pending human review')
  assert(html.includes('border-[var(--color-warn-line)]'), '2.7: Stage 6 uses warn tone border styling')
}

// 2.8: ESCROW HOLD on authorized + none (pre-evaluation hold)
{
  const p = makePromise({
    payment: { state: 'authorized' },
    gate_decision: {
      outcome: 'none',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [],
    },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('ESCROW HOLD'), '2.8: Stage 6 displays ESCROW HOLD badge')
  assert(html.includes('Funds secured in escrow'), '2.8: Stage 6 indicates Funds secured in escrow')
  assert(html.includes('Escrow Authorization Active'), '2.8: Header banner indicates Escrow Authorization Active')
}

// 2.9: Pending settlement before authorization (created state)
{
  const p = makePromise({
    payment: { state: 'created', authorization_id: null },
  })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('Awaiting invariant gate'), '2.9: Stage 6 displays Awaiting invariant gate before auth')
}

// =========================================================================
// SECTION 3: Truncated Hash Display for RFC 8785 Receipt
// =========================================================================
console.log('\n--- SECTION 3: Truncated Hash Display for RFC 8785 Receipt ---')

// 3.1: Proper SHA-256 formatting with prefix
{
  const fullHash = 'sha256:4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123'
  const p = makePromise({ receipt_hash: fullHash })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('sha256:4a5b6c7d…'), '3.1: Formatted with sha256: prefix, 8 hex digits, and ellipsis')
  assert(fullHash.replace('sha256:', '').length === 64, '3.1: Full hash is exactly 64 hex characters (32 bytes)')
}

// 3.2: Raw 64-char hex without sha256: prefix
{
  const rawHex = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
  const p = makePromise({ receipt_hash: rawHex })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('sha256:e3b0c442…'), '3.2: Raw hex correctly normalized to sha256: prefix and truncated to 8 chars')
  assert(rawHex.length === 64, '3.2: Raw hex length is 64 characters')
}

// 3.3: Missing receipt_hash (empty or undefined)
{
  const p = makePromise({ receipt_hash: '' })
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  assert(html.includes('Awaiting seal'), '3.3: Empty hash renders Awaiting seal')
  assert(html.includes('Draft'), '3.3: Empty hash displays Draft badge')
}

// =========================================================================
// SECTION 4: Mobile Viewport Responsiveness (375px)
// =========================================================================
console.log('\n--- SECTION 4: Mobile Viewport Responsiveness (375px) ---')

{
  const p = makePromise()
  const html = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={p} />)
  // Verify horizontal swipe track classes
  assert(html.includes('overflow-x-auto'), '4.1: Outer track specifies overflow-x-auto for horizontal swipe')
  assert(html.includes('min-w-[720px]'), '4.2: Inner stage container enforces min-w-[720px] preventing crushed columns on 375px viewports')
  assert(html.includes('sm:min-w-0'), '4.3: Reset min-w on sm breakpoint (desktop)')
  assert(html.includes('sm:grid sm:grid-cols-6'), '4.4: 6-column grid applied at sm breakpoint (>=640px)')
}

// =========================================================================
// SECTION 5: Two-Lane Start Page (Start.tsx)
// =========================================================================
console.log('\n--- SECTION 5: Two-Lane Start Page (Start.tsx) ---')

{
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  const html = ReactDOMServer.renderToStaticMarkup(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <StartPage />
      </MemoryRouter>
    </QueryClientProvider>
  )

  // Lane 1 Verification
  assert(html.includes('Real PayPal Sandbox'), '5.1: Lane 1 displays Real PayPal Sandbox badge')
  assert(html.includes('Lane 1'), '5.1: Lane 1 identifier rendered')
  assert(html.includes('Real PayPal Sandbox Flow'), '5.1: Lane 1 title rendered')
  assert(html.includes('sb-buyer-promiseloop@personal.example.com'), '5.1: Copyable sandbox buyer email present')
  assert(html.includes('Password1!'), '5.1: Copyable sandbox buyer password present')
  assert(html.includes('Copy buyer sandbox email'), '5.1: Copy email button has accessible aria-label')
  assert(html.includes('Copy buyer sandbox password'), '5.1: Copy password button has accessible aria-label')
  assert(html.includes('Launch Real Sandbox Flow →'), '5.1: Primary CTA button to launch sandbox flow present')

  // Lane 2 Verification
  assert(html.includes('Instant 30-sec Demo'), '5.2: Lane 2 displays Instant 30-sec Demo badge')
  assert(html.includes('Lane 2'), '5.2: Lane 2 identifier rendered')
  assert(html.includes('Instant 30-Sec Evaluation'), '5.2: Lane 2 title rendered')
  assert(html.includes('1-click deterministic execution'), '5.2: Lane 2 value proposition described')
  assert(html.includes('Run Instant Demo Scenario →'), '5.2: 1-click execution CTA present')
  assert(html.includes('View verification proof &amp; metrics →') || html.includes('View verification proof & metrics →'), '5.2: Secondary link to /proof present')

  // Preserved Guides
  assert(html.includes('How to test (5 minutes)'), '5.3: 5-minute walkthrough guide preserved')
  assert(html.includes('What is simulated vs real'), '5.3: Boundary disclosure card preserved')
  assert(html.includes('Real Systems'), '5.3: Boundary disclosure lists Real Systems')
  assert(html.includes('Simulated (SYNTHETIC)'), '5.3: Boundary disclosure lists Simulated Systems')
}

// =========================================================================
// SECTION 6: Sidebar Navigation & Drift Counter (Sidebar.tsx)
// =========================================================================
console.log('\n--- SECTION 6: Sidebar Navigation & Drift Counter ---')

// 6.1: Core Flow and Audit navigation links
{
  const html = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/']}>
      <Sidebar driftCount={0} />
    </MemoryRouter>
  )

  assert(html.includes('Core Flow'), '6.1: Sidebar renders Core Flow section heading')
  assert(html.includes('Start / Overview'), '6.1: Core Flow contains Start / Overview')
  assert(html.includes('Shopper Agent'), '6.1: Core Flow contains Shopper Agent')
  assert(html.includes('Promise Receipts'), '6.1: Core Flow contains Promise Receipts')
  assert(html.includes('Control Tower'), '6.1: Core Flow contains Control Tower')
  assert(html.includes('Drift Queue'), '6.1: Core Flow contains Drift Queue')
  assert(html.includes('Proof &amp; Metrics') || html.includes('Proof & Metrics'), '6.1: Core Flow contains Proof & Metrics')

  assert(html.includes('Audit &amp; Diagnostics') || html.includes('Audit & Diagnostics'), '6.2: Sidebar renders Audit & Diagnostics section heading')
  assert(html.includes('Event History'), '6.2: Audit contains Event History')
  assert(html.includes('Receipt Verifier'), '6.2: Audit contains Receipt Verifier')
  assert(html.includes('Spine Console'), '6.2: Audit contains Spine Console')
}

// 6.2: Drift Badge Count Display (driftCount > 0 vs driftCount === 0)
{
  const htmlWithDrift = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/']}>
      <Sidebar driftCount={7} />
    </MemoryRouter>
  )
  assert(htmlWithDrift.includes('>7<') || htmlWithDrift.includes('7 open drift cases'), '6.3: Renders drift badge with count 7 when driftCount = 7')
  assert(htmlWithDrift.includes('aria-label="7 open drift cases"'), '6.3: Renders accessible aria-label for drift badge')

  const htmlNoDrift = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/']}>
      <Sidebar driftCount={0} />
    </MemoryRouter>
  )
  assert(!htmlNoDrift.includes('open drift cases'), '6.4: Does not render drift badge when driftCount = 0')

  const htmlNegativeDrift = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/']}>
      <Sidebar driftCount={-1} />
    </MemoryRouter>
  )
  assert(!htmlNegativeDrift.includes('open drift cases'), '6.5: Does not render drift badge when driftCount is negative')
}

// 6.3: Mobile Drawer Responsiveness
{
  const htmlMobileOpen = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/']}>
      <Sidebar isMobileOpen={true} />
    </MemoryRouter>
  )
  assert(htmlMobileOpen.includes('fixed inset-0 z-40 bg-slate-900/40'), '6.6: Renders mobile backdrop when isMobileOpen is true')
  assert(htmlMobileOpen.includes('Close sidebar'), '6.6: Renders close sidebar button when isMobileOpen is true')
}

// =========================================================================
// SECTION 7: Adversarial Edge Cases & Fallback Resiliency
// =========================================================================
console.log('\n--- SECTION 7: Adversarial Edge Cases & Fallback Resiliency ---')

// 7.1: Stage 3 Payment failure states
{
  const pExpired = makePromise({
    payment: { state: 'expired', authorization_id: null },
  })
  const htmlExpired = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={pExpired} />)
  assert(htmlExpired.includes('EXPIRED'), '7.1: Stage 3 displays EXPIRED badge when payment expired')
  assert(htmlExpired.includes('Authorization expired or failed'), '7.1: Stage 3 detail reflects expired/failed state')

  const pFailed = makePromise({
    payment: { state: 'failed', authorization_id: null },
  })
  const htmlFailed = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={pFailed} />)
  assert(htmlFailed.includes('FAILED'), '7.2: Stage 3 displays FAILED badge when payment failed')
}

// 7.2: Stage 3 Authorization amount fallback when auth ID is missing but amount present
{
  const pNoAuthId = makePromise({
    payment: { state: 'authorized', authorization_id: null, amount_cents: 108142 },
  })
  const htmlNoAuthId = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={pNoAuthId} />)
  assert(htmlNoAuthId.includes('$1081.42 Hold'), '7.3: Stage 3 displays dollar hold amount when auth ID is missing')
}

// 7.3: Stage 5 multiple findings order
{
  const pMultiFindings = makePromise({
    gate_decision: {
      outcome: 'DRIFT',
      receipt_hash: 'sha256:1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff',
      evaluated_at: '2026-11-02T14:00:00Z',
      rules_version: '2026.11',
      findings: [
        { code: 'INV-PRIMARY', invariant: 'product', severity: 'DRIFT', expected: 'New', observed: 'Used', title: 'Primary Finding Code', explanation: 'First' },
        { code: 'INV-SECONDARY', invariant: 'spending', severity: 'DRIFT', expected: 100, observed: 200, title: 'Secondary Finding Code', explanation: 'Second' },
      ],
    },
  })
  const htmlMulti = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={pMultiFindings} />)
  assert(htmlMulti.includes('INV-PRIMARY'), '7.4: Stage 5 prioritizes primary finding code (index 0)')
  assert(htmlMulti.includes('Primary Finding Code'), '7.4: Stage 5 prioritizes primary finding title (index 0)')
}

// 7.4: Stage 1 fallback when constraints are empty or product_type is null
{
  const pEmptyConstraints = makePromise({
    constraints: { product_type: '', condition: '' },
  })
  const htmlEmptyConstraints = ReactDOMServer.renderToStaticMarkup(<PromiseProgressionHUD promise={pEmptyConstraints} />)
  assert(htmlEmptyConstraints.includes('Buyer approved specification'), '7.5: Stage 1 displays fallback Buyer approved specification')
}

// =========================================================================
// SECTION 8: Active Link Resolution in Sidebar (Sidebar.tsx)
// =========================================================================
console.log('\n--- SECTION 8: Active Link Resolution in Sidebar ---')

// 8.1: /tower vs /tower?filter=drift disambiguation
{
  // When at /tower without query, Control Tower must be active and Drift Queue must NOT be active
  const htmlTower = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/tower']}>
      <Sidebar driftCount={0} />
    </MemoryRouter>
  )
  assert(
    htmlTower.includes('class="flex items-center justify-between h-10 px-3 rounded-[var(--radius-control)] text-[14px] transition-all duration-150 bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-semibold shadow-2xs" href="/tower"'),
    '8.1: Control Tower link is active when pathname is /tower'
  )

  // When at /tower?filter=drift, Drift Queue must be active and Control Tower must NOT be active
  const htmlDrift = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/tower?filter=drift']}>
      <Sidebar driftCount={2} />
    </MemoryRouter>
  )
  assert(
    htmlDrift.includes('class="flex items-center justify-between h-10 px-3 rounded-[var(--radius-control)] text-[14px] transition-all duration-150 bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-semibold shadow-2xs" href="/tower?filter=drift"'),
    '8.2: Drift Queue link is active when search has filter=drift'
  )

  // When at /tower/cases/:id, Drift Queue must also be active
  const htmlCase = ReactDOMServer.renderToStaticMarkup(
    <MemoryRouter initialEntries={['/tower/cases/PL-CHALLENGER']}>
      <Sidebar driftCount={2} />
    </MemoryRouter>
  )
  assert(
    htmlCase.includes('class="flex items-center justify-between h-10 px-3 rounded-[var(--radius-control)] text-[14px] transition-all duration-150 bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-semibold shadow-2xs" href="/tower?filter=drift"'),
    '8.3: Drift Queue link is active when inspecting case at /tower/cases/:id'
  )
}

// =========================================================================
// SECTION 9: Mounting Verification on Receipt & DriftReview
// =========================================================================
console.log('\n--- SECTION 9: Mounting Verification in Receipt & DriftReview ---')

import fs from 'fs'
import path from 'path'

{
  const receiptSrc = fs.readFileSync(path.resolve('src/pages/Receipt.tsx'), 'utf-8')
  assert(
    receiptSrc.includes('<PromiseProgressionHUD promise={promise} />'),
    '9.1: Receipt.tsx mounts PromiseProgressionHUD with promise prop'
  )
  assert(
    receiptSrc.includes("import { PromiseProgressionHUD } from '../components/domain/PromiseProgressionHUD'"),
    '9.1: Receipt.tsx imports PromiseProgressionHUD cleanly'
  )

  const driftReviewSrc = fs.readFileSync(path.resolve('src/pages/DriftReview.tsx'), 'utf-8')
  assert(
    driftReviewSrc.includes('<PromiseProgressionHUD promise={promise} />'),
    '9.2: DriftReview.tsx mounts PromiseProgressionHUD with promise prop'
  )
  assert(
    driftReviewSrc.includes("import { PromiseProgressionHUD } from '../components/domain/PromiseProgressionHUD'"),
    '9.2: DriftReview.tsx imports PromiseProgressionHUD cleanly'
  )
}

console.log(`\n=================================================`)
console.log(`EMPIRICAL CHALLENGER RESULTS: ${passed} PASSED, ${failed} FAILED`)
console.log(`=================================================`)

if (failed > 0) {
  process.exit(1)
}

