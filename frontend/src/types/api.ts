export type PaymentState =
  | 'created'
  | 'approved'
  | 'authorized'
  | 'capturing'
  | 'capture_pending'
  | 'captured'
  | 'voided'
  | 'expired'
  | 'failed'

export type GateOutcome = 'MATCH' | 'DRIFT' | 'HOLD' | 'PROHIBITED' | 'none'

export type ReceiptStatus = 'draft' | 'approved' | 'stale' | 'superseded' | 'rejected'

export type TrustLevel = 'merchant_system' | 'carrier' | 'claim'

export interface Finding {
  code: string
  invariant: 'product' | 'spending' | 'merchant' | 'promise' | 'evidence' | 'financial' | 'execution' | 'decision'
  severity: 'DRIFT' | 'HOLD' | 'INFO'
  expected: unknown
  observed: unknown
  title: string
  explanation: string
  evidence_ids?: string[]
}

export interface Decision {
  outcome: GateOutcome
  findings: Finding[]
  receipt_hash: string
  evaluated_at: string
  rules_version: string
}

export interface IntentConstraints {
  product_type: string
  condition: string
  variant_color: string
  max_total_cents: number
  currency: string
  deadline_days: number
  substitution_allowed: boolean
  resolved_deadline_at: string
}

export interface ProductCandidate {
  id: string
  title: string
  brand: string
  price_cents: number
  currency: string
  condition: string | null
  image_url: string
  merchant_domain: string
  variants: string[]
  raw_sha256: string
}

export interface MerchantQuote {
  seller_name: string
  seller_domain: string
  subtotal_cents: number
  shipping_cents: number
  tax_cents: number
  total_cents: number
  currency: string
  promised_delivery_at: string
  raw_sha256: string
}

export interface FulfillmentEvent {
  id: string
  seq: number
  source: string
  source_type: TrustLevel
  synthetic: boolean
  event_type: string
  occurred_at: string
  recorded_at: string
  status_display: string
  payload: Record<string, unknown>
  diff_summary?: {
    expected: string
    observed: string
  }
}

export interface LifecycleStepItem {
  id: string
  title: string
  time: string
  source: string
  ref_id?: string
  state: 'done' | 'current' | 'failed' | 'pending'
}

export interface PaymentDetails {
  order_id: string | null
  authorization_id: string | null
  capture_id: string | null
  state: PaymentState
  amount_cents: number
  currency: string
  is_simulated?: boolean
  expiration_time: string | null
  honor_until: string | null
  captured_at: string | null
  voided_at: string | null
  void_reason: string | null
  updated_at: string
}

export interface Counterfactual {
  naive_capture_cents: number
  gated_capture_cents: number
  loss_avoided_cents: number
  simulated?: boolean
}

export interface ProofProtected {
  loss_avoided_cents: number
  scenarios_blocked: number
  simulated: boolean
}

export interface PurchasePromise {
  id: string
  ref: string // PL-XXXXXX
  version: number
  status: ReceiptStatus
  buyer_instruction: string
  instruction_source: 'ai' | 'fallback'
  constraints: IntentConstraints
  product_snapshot: ProductCandidate
  merchant_quote: MerchantQuote
  receipt_hash: string
  approved_at: string | null
  payment: PaymentDetails
  gate_decision: Decision | null
  evidence_events: FulfillmentEvent[]
  lifecycle: LifecycleStepItem[]
  counterfactual?: Counterfactual
  created_at: string
  updated_at: string
}

export interface ReplayAuditStep {
  n: number
  title: string
  source: string
  occurred_at: string
  recorded_at: string
  ids: string[]
  hash?: string
  divergence: boolean
  finding?: Finding
  details?: Record<string, unknown>
}

export interface ReplayData {
  purchase_id: string
  ref: string
  chain_intact: boolean
  event_count: number
  broken_at_step?: number
  artifacts_verified: string // e.g. "3/3"
  custom_id_matches: boolean
  steps: ReplayAuditStep[]
  counterfactual?: Counterfactual
}

export interface TowerKPIs {
  active_promises: number
  verified_outcomes_pct: number
  review_required: number
  authorized_not_captured_cents: number
  authorized_not_captured_count: number
  loss_avoided_cents?: number
  loss_avoided_simulated?: boolean
}

export interface ProofMetric {
  title: string
  numerator: number | string
  denominator: number | string
  unit?: string
  definition: string
  source_run: string
}

export interface ProofScenario {
  id: string
  name: string
  category: string
  expected_outcome: string
  actual_outcome: string
  finding_codes: string[]
  passed: boolean
  counterfactual?: Counterfactual
}

export interface LedgerEventItem {
  seq: number
  purchase_id: string
  purchase_ref: string
  type: string
  source: string
  actor: string
  recorded_at: string
  payload_summary: string
  hash: string
  status_pill: {
    label: string
    tone: 'ok' | 'warn' | 'bad' | 'neutral' | 'info'
  }
}

