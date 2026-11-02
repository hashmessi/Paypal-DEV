import type { PaymentState, GateOutcome, ReceiptStatus, TrustLevel, Finding } from '../types/api'

export type PillTone = 'ok' | 'warn' | 'bad' | 'neutral' | 'info'

export interface StatusPillInfo {
  label: string
  tone: PillTone
  icon?: string
  code?: string
  isUppercase?: boolean
}

/**
 * Single source of truth for UI-SPEC Status Vocabulary
 */
export function getAuthorizationPill(state: PaymentState): StatusPillInfo {
  switch (state) {
    case 'created':
      return { label: 'Order created', tone: 'neutral' }
    case 'approved':
      return { label: 'Approved', tone: 'neutral' }
    case 'authorized':
      return { label: 'Authorized · not captured', tone: 'warn' }
    case 'capturing':
      return { label: 'Capturing', tone: 'info' }
    case 'capture_pending':
      return { label: 'Capture pending', tone: 'warn' }
    case 'captured':
      return { label: 'Captured', tone: 'ok' }
    case 'voided':
      return { label: 'Voided', tone: 'neutral' }
    case 'expired':
      return { label: 'Expired', tone: 'bad' }
    case 'failed':
      return { label: 'Failed', tone: 'bad' }
    default:
      return { label: state, tone: 'neutral' }
  }
}

export function getGatePill(outcome: GateOutcome | null | undefined, findings?: Finding[]): StatusPillInfo {
  if (!outcome || outcome === 'none') {
    return { label: 'Awaiting evidence', tone: 'neutral' }
  }

  const primaryFinding = findings && findings.length > 0 ? findings[0] : undefined

  switch (outcome) {
    case 'MATCH':
      return { label: 'Verified', tone: 'ok' }
    case 'DRIFT':
      return {
        label: primaryFinding?.title || 'Condition mismatch',
        tone: 'bad',
        icon: 'octagon-alert',
        code: primaryFinding?.code || 'CONDITION_MISMATCH',
      }
    case 'HOLD':
      return {
        label: primaryFinding?.title || 'Awaiting carrier',
        tone: 'warn',
        code: primaryFinding?.code || 'CARRIER_ACCEPTANCE_MISSING',
      }
    case 'PROHIBITED':
      return {
        label: 'Capture prohibited',
        tone: 'bad',
        code: primaryFinding?.code || 'AUTH_EXPIRED',
      }
    default:
      return { label: 'Awaiting evidence', tone: 'neutral' }
  }
}

export function getReceiptPill(status: ReceiptStatus): StatusPillInfo {
  switch (status) {
    case 'draft':
      return { label: 'Draft', tone: 'neutral' }
    case 'approved':
      return { label: 'Approved', tone: 'ok' }
    case 'stale':
      return { label: 'Stale · reapproval required', tone: 'warn' }
    case 'superseded':
      return { label: 'Superseded', tone: 'neutral' }
    case 'rejected':
      return { label: 'Rejected', tone: 'bad' }
    default:
      return { label: status, tone: 'neutral' }
  }
}

/**
 * Promise state header pill (UI-02)
 * Rendered in uppercase:
 * - AUTHORIZED · NOT CAPTURED
 * - CAPTURE BLOCKED
 * - CAPTURED
 */
export function getPromiseStateHeaderPill(paymentState: PaymentState, gateOutcome?: GateOutcome): StatusPillInfo {
  if (paymentState === 'captured') {
    return { label: 'CAPTURED', tone: 'ok', isUppercase: true }
  }

  if (gateOutcome === 'DRIFT' || gateOutcome === 'PROHIBITED') {
    return { label: 'CAPTURE BLOCKED', tone: 'bad', isUppercase: true, icon: 'octagon-alert' }
  }

  if (paymentState === 'voided') {
    return { label: 'VOIDED', tone: 'neutral', isUppercase: true }
  }

  if (paymentState === 'expired') {
    return { label: 'EXPIRED', tone: 'bad', isUppercase: true }
  }

  return { label: 'AUTHORIZED · NOT CAPTURED', tone: 'warn', isUppercase: true }
}

export function getTrustBadge(trust: TrustLevel): { label: string; tone: PillTone; note?: string } {
  switch (trust) {
    case 'merchant_system':
      return { label: 'merchant_system', tone: 'neutral' }
    case 'carrier':
      return { label: 'carrier', tone: 'neutral' }
    case 'claim':
      return { label: 'claim', tone: 'warn', note: 'can only hold' }
    default:
      return { label: trust, tone: 'neutral' }
  }
}

