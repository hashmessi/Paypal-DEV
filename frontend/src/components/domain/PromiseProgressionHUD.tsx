import React from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  Clock,
  Lock,
  Unlock,
  AlertOctagon,
  FileText,
  Fingerprint,
  CreditCard,
  PackageCheck,
  ShieldAlert,
  Coins,
} from 'lucide-react'
import type { PurchasePromise } from '../../types/api'

export interface PromiseProgressionHUDProps {
  promise: PurchasePromise
  className?: string
}

type StageTone = 'ok' | 'bad' | 'warn' | 'neutral' | 'info'

interface StageItem {
  id: string
  step: number
  title: string
  badge: string
  detail: string
  tone: StageTone
  icon: React.ComponentType<{ className?: string }>
}

export const PromiseProgressionHUD: React.FC<PromiseProgressionHUDProps> = ({
  promise,
  className = '',
}) => {
  const { constraints, receipt_hash, payment, evidence_events, gate_decision } = promise

  const evidenceCount = evidence_events?.length ?? 0
  const outcome = gate_decision?.outcome ?? 'none'
  const primaryFinding = gate_decision?.findings && gate_decision.findings.length > 0 ? gate_decision.findings[0] : null
  const paymentState = payment?.state ?? 'created'
  const isAuthHeld = Boolean(payment?.authorization_id) || ['authorized', 'capturing', 'capture_pending', 'captured', 'voided'].includes(paymentState)

  // Stage 1: Intent & Constraints
  const stage1: StageItem = {
    id: 'intent',
    step: 1,
    title: 'Intent & Constraints',
    badge: 'Frozen',
    detail: constraints?.product_type
      ? `${constraints.product_type} · ${constraints.condition || 'exact specs'}`
      : 'Buyer approved specification',
    tone: 'ok',
    icon: FileText,
  }

  // Stage 2: RFC 8785 Receipt
  const hashDisplay = receipt_hash
    ? `sha256:${receipt_hash.replace(/^sha256:/, '').slice(0, 8)}…`
    : 'Awaiting seal'
  const stage2: StageItem = {
    id: 'receipt',
    step: 2,
    title: 'RFC 8785 Receipt',
    badge: receipt_hash ? 'Sealed' : 'Draft',
    detail: hashDisplay,
    tone: receipt_hash ? 'ok' : 'neutral',
    icon: Fingerprint,
  }

  // Stage 3: PayPal Authorization
  let stage3Tone: StageTone = 'neutral'
  let stage3Badge = 'Pending'
  let stage3Detail = 'Awaiting customer hold'
  let stage3Icon: React.ComponentType<{ className?: string }> = CreditCard

  if (isAuthHeld) {
    stage3Tone = 'ok'
    stage3Badge = paymentState === 'captured' ? 'Settled' : paymentState === 'voided' ? 'Released' : 'Held'
    stage3Detail = payment?.authorization_id
      ? `Auth · ${payment.authorization_id.slice(0, 9)}…`
      : payment?.amount_cents
        ? `$${(payment.amount_cents / 100).toFixed(2)} Hold`
        : 'Authorization active'
    stage3Icon = CheckCircle2
  } else if (paymentState === 'failed' || paymentState === 'expired') {
    stage3Tone = 'bad'
    stage3Badge = paymentState.toUpperCase()
    stage3Detail = 'Authorization expired or failed'
    stage3Icon = AlertOctagon
  } else {
    stage3Tone = 'warn'
    stage3Badge = 'Awaiting Hold'
    stage3Detail = 'Orders v2 auth needed'
    stage3Icon = Clock
  }

  const stage3: StageItem = {
    id: 'auth',
    step: 3,
    title: 'PayPal Authorization',
    badge: stage3Badge,
    detail: stage3Detail,
    tone: stage3Tone,
    icon: stage3Icon,
  }

  // Stage 4: Evidence Ingestion
  let stage4Tone: StageTone = 'neutral'
  let stage4Badge = 'Awaiting Scans'
  let stage4Detail = 'Awaiting warehouse/carrier'
  let stage4Icon: React.ComponentType<{ className?: string }> = PackageCheck

  if (evidenceCount > 0) {
    stage4Tone = 'ok'
    stage4Badge = `${evidenceCount} Ingested`
    stage4Detail = `${evidenceCount} telemetry event${evidenceCount > 1 ? 's' : ''} logged`
    stage4Icon = CheckCircle2
  } else {
    stage4Tone = 'neutral'
    stage4Badge = '0 Events'
    stage4Detail = 'Awaiting warehouse pick'
    stage4Icon = Clock
  }

  const stage4: StageItem = {
    id: 'evidence',
    step: 4,
    title: 'Evidence Ingestion',
    badge: stage4Badge,
    detail: stage4Detail,
    tone: stage4Tone,
    icon: stage4Icon,
  }

  // Stage 5: Drift Invariant Gate
  let stage5Tone: StageTone = 'neutral'
  let stage5Badge = 'Pending'
  let stage5Detail = 'Awaiting telemetry'
  let stage5Icon: React.ComponentType<{ className?: string }> = ShieldAlert

  if (outcome === 'DRIFT') {
    stage5Tone = 'bad'
    stage5Badge = primaryFinding?.code || 'DRIFT'
    stage5Detail = primaryFinding?.title || 'Condition Mismatch detected'
    stage5Icon = AlertTriangle
  } else if (outcome === 'MATCH') {
    stage5Tone = 'ok'
    stage5Badge = 'MATCH'
    stage5Detail = 'All 8 invariants verified'
    stage5Icon = CheckCircle2
  } else if (outcome === 'HOLD') {
    stage5Tone = 'warn'
    stage5Badge = 'HOLD'
    stage5Detail = primaryFinding?.title || 'Operator hold active'
    stage5Icon = Clock
  } else if (evidenceCount > 0) {
    stage5Tone = 'warn'
    stage5Badge = 'Evaluating'
    stage5Detail = 'Evaluating invariants'
    stage5Icon = Clock
  }

  const stage5: StageItem = {
    id: 'gate',
    step: 5,
    title: 'Drift Invariant Gate',
    badge: stage5Badge,
    detail: stage5Detail,
    tone: stage5Tone,
    icon: stage5Icon,
  }

  // Stage 6: Gated Settlement
  let stage6Tone: StageTone = 'neutral'
  let stage6Badge = 'Pending'
  let stage6Detail = 'Awaiting invariant gate'
  let stage6Icon: React.ComponentType<{ className?: string }> = Coins

  if (paymentState === 'captured') {
    stage6Tone = 'ok'
    stage6Badge = 'CAPTURED'
    stage6Detail = payment.captured_at ? 'Funds settled to merchant' : 'Captured via live Orders v2'
    stage6Icon = CheckCircle2
  } else if (paymentState === 'voided') {
    stage6Tone = 'neutral'
    stage6Badge = 'VOIDED'
    stage6Detail = payment.void_reason || 'Authorization released'
    stage6Icon = CheckCircle2
  } else if (paymentState === 'authorized') {
    if (outcome === 'DRIFT') {
      stage6Tone = 'bad'
      stage6Badge = 'CAPTURE BLOCKED'
      stage6Detail = 'Hold locked · settlement blocked'
      stage6Icon = Lock
    } else if (outcome === 'MATCH') {
      stage6Tone = 'ok'
      stage6Badge = 'READY TO CAPTURE'
      stage6Detail = 'Pre-cleared · capture permitted'
      stage6Icon = Unlock
    } else if (outcome === 'HOLD') {
      stage6Tone = 'warn'
      stage6Badge = 'SETTLEMENT HOLD'
      stage6Detail = 'Held pending human review'
      stage6Icon = Lock
    } else {
      stage6Tone = 'info'
      stage6Badge = 'ESCROW HOLD'
      stage6Detail = 'Funds secured in escrow'
      stage6Icon = Lock
    }
  }

  const stage6: StageItem = {
    id: 'settlement',
    step: 6,
    title: 'Gated Settlement',
    badge: stage6Badge,
    detail: stage6Detail,
    tone: stage6Tone,
    icon: stage6Icon,
  }

  const stages = [stage1, stage2, stage3, stage4, stage5, stage6]

  const getToneClasses = (tone: StageTone) => {
    switch (tone) {
      case 'ok':
        return {
          card: 'border-[var(--color-ok-line)] bg-[var(--color-ok-soft)]/50',
          step: 'bg-[var(--color-ok)] text-white',
          badge: 'bg-[var(--color-ok-soft)] text-[var(--color-ok)] border-[var(--color-ok-line)]',
          icon: 'text-[var(--color-ok)]',
        }
      case 'bad':
        return {
          card: 'border-[var(--color-bad-line)] bg-[var(--color-bad-soft)]/60',
          step: 'bg-[var(--color-bad)] text-white',
          badge: 'bg-[var(--color-bad-soft)] text-[var(--color-bad)] border-[var(--color-bad-line)]',
          icon: 'text-[var(--color-bad)]',
        }
      case 'warn':
        return {
          card: 'border-[var(--color-warn-line)] bg-[var(--color-warn-soft)]/50',
          step: 'bg-[var(--color-warn)] text-white',
          badge: 'bg-[var(--color-warn-soft)] text-[var(--color-warn)] border-[var(--color-warn-line)]',
          icon: 'text-[var(--color-warn)]',
        }
      case 'info':
        return {
          card: 'border-[var(--color-accent-line)] bg-[var(--color-accent-soft)]/50',
          step: 'bg-[var(--color-accent)] text-white',
          badge: 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] border-[var(--color-accent-line)]',
          icon: 'text-[var(--color-accent)]',
        }
      case 'neutral':
      default:
        return {
          card: 'border-[var(--color-line)] bg-[var(--color-surface)]',
          step: 'bg-[var(--color-neutral-soft)] text-[var(--color-muted)] border border-[var(--color-line)]',
          badge: 'bg-[var(--color-neutral-soft)] text-[var(--color-muted)] border-[var(--color-line)]',
          icon: 'text-[var(--color-muted)]',
        }
    }
  }

  return (
    <div
      className={`p-4 rounded-[var(--radius-card)] bg-white border border-[var(--color-line)] shadow-[var(--shadow-card)] space-y-3 ${className}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5 border-b border-[var(--color-line)] pb-2.5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--color-accent)]">
            Canonical Execution Loop
          </p>
          <h3 className="text-[14px] font-semibold text-[var(--color-ink)]">
            6-Stage Promise Progression HUD
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {outcome === 'DRIFT' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)] animate-pulse">
              <AlertTriangle className="w-3 h-3" /> Invariant Drift Detected
            </span>
          )}
          {outcome === 'MATCH' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-ok-soft)] text-[var(--color-ok)] border border-[var(--color-ok-line)]">
              <CheckCircle2 className="w-3 h-3" /> Invariants Verified
            </span>
          )}
          {paymentState === 'captured' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-ok-soft)] text-[var(--color-ok)] border border-[var(--color-ok-line)]">
              <Coins className="w-3 h-3" /> Settled to Merchant
            </span>
          )}
          {paymentState === 'authorized' && outcome === 'none' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-accent-soft)] text-[var(--color-accent)] border border-[var(--color-accent-line)]">
              <Lock className="w-3 h-3" /> Escrow Authorization Active
            </span>
          )}
        </div>
      </div>

      {/* Responsive Horizontal Scroll on Mobile (<640px) & 6-Col Grid on Desktop */}
      <div className="overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin">
        <div className="flex items-stretch gap-2.5 min-w-[720px] sm:min-w-0 sm:grid sm:grid-cols-6">
          {stages.map((st) => {
            const toneStyles = getToneClasses(st.tone)
            const StageIcon = st.icon

            return (
              <div
                key={st.id}
                className={`flex-1 rounded-[var(--radius-control)] border p-2.5 sm:p-3 flex flex-col justify-between transition-all ${toneStyles.card}`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1.5 mb-2">
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${toneStyles.step}`}
                    >
                      {st.step}
                    </span>
                    <span
                      className={`text-[9.5px] font-mono font-semibold px-1.5 py-0.5 rounded-full uppercase border shrink-0 tracking-tight ${toneStyles.badge}`}
                    >
                      {st.badge}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 mb-1">
                    <StageIcon className={`w-3.5 h-3.5 shrink-0 ${toneStyles.icon}`} />
                    <span className="text-[12px] font-semibold text-[var(--color-ink)] leading-snug">
                      {st.title}
                    </span>
                  </div>
                </div>

                <p
                  className="text-[11px] text-[var(--color-muted)] leading-tight mt-1 line-clamp-2"
                  title={st.detail}
                >
                  {st.detail}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
