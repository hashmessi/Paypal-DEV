import React from 'react'
import { Card } from '../ui/Card'
import { HashChip } from '../ui/HashChip'
import { StatusPill, AuthorizationPill } from './StatusPill'
import { formatMinor } from '../../lib/money'
import type { PurchasePromise } from '../../types/api'

export interface TruthPanelProps {
  promise: PurchasePromise
  children?: React.ReactNode
  className?: string
}

export const TruthPanel: React.FC<TruthPanelProps> = ({
  promise,
  children,
  className = '',
}) => {
  const isLive =
    promise.payment.is_simulated === false ||
    promise.counterfactual?.simulated === false

  const liveBadge = isLive ? (
    <StatusPill tone="ok" dot={true}>
      PayPal Sandbox · live API
    </StatusPill>
  ) : (
    <StatusPill tone="info" dot={true}>
      Simulated gateway
    </StatusPill>
  )

  const captureStatus = promise.payment.capture_id ? (
    <HashChip value={promise.payment.capture_id} kind="paypal" full />
  ) : promise.payment.state === 'voided' ? (
    <span className="text-[var(--color-muted)] text-[13px]">Voided</span>
  ) : promise.gate_decision?.outcome === 'DRIFT' ? (
    <span className="text-[var(--color-bad)] text-[13px] font-semibold">Blocked by drift gate</span>
  ) : (
    <span className="text-[var(--color-muted)] text-[13px]">Not submitted</span>
  )

  const isVoided =
    promise.payment.state === 'voided' ||
    Boolean(promise.payment.void_reason) ||
    Boolean(promise.payment.voided_at)

  return (
    <Card
      padding="md"
      title="PayPal transaction"
      subtitle={isLive ? 'Real Orders v2 & Payments v2 Sandbox' : 'Simulated Orders v2 gateway'}
      action={liveBadge}
      className={className}
    >
      <div className="space-y-4">
        {/* Amount + State Pill */}
        <div className="p-4 rounded-xl bg-gradient-to-br from-[#003087]/5 to-[#0070ba]/10 border border-[#0070ba]/20 flex items-center justify-between">
          <div>
            <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
              {promise.payment.state === 'voided'
                ? 'Released hold'
                : promise.payment.state === 'captured'
                  ? 'Captured settlement'
                  : 'Authorized settlement hold'}
            </p>
            <p className="text-[28px] font-semibold tabular-nums text-[var(--color-ink)] leading-tight mt-0.5">
              {formatMinor(promise.payment.amount_cents)}{' '}
              <span className="text-[18px] text-[var(--color-muted)] font-normal">
                {promise.payment.currency}
              </span>
            </p>
          </div>
          <AuthorizationPill state={promise.payment.state} />
        </div>

        {/* Transaction ID rows */}
        <div className="space-y-2 text-[14px]">
          <div className="flex items-center justify-between">
            <span className="text-[var(--color-muted)]">Order ID</span>
            {promise.payment.order_id ? (
              <HashChip value={promise.payment.order_id} kind="paypal" full />
            ) : (
              <span className="text-[var(--color-muted)] text-[13px]">
                {promise.payment.state === 'created' ? 'Awaiting order' : 'N/A'}
              </span>
            )}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[var(--color-muted)]">Authorization ID</span>
            {promise.payment.authorization_id ? (
              <HashChip value={promise.payment.authorization_id} kind="paypal" full />
            ) : (
              <span className="text-[var(--color-muted)] text-[13px]">N/A</span>
            )}
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[var(--color-muted)]">Payment state</span>
            <span className="font-medium text-[var(--color-ink)] text-[13px] capitalize">
              {promise.payment.state.replace('_', ' ')}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[var(--color-muted)]">Capture ID</span>
            {captureStatus}
          </div>

          {isVoided && (
            <div className="p-3 rounded-[var(--radius-control)] bg-[var(--color-bad-soft)] border border-[var(--color-bad-line)] space-y-1.5 text-[12px] mt-2">
              <div className="flex items-center justify-between text-[var(--color-bad)] font-semibold">
                <span>Authorization voided</span>
                {promise.payment.voided_at && (
                  <span className="font-mono text-[11px] opacity-90">
                    {promise.payment.voided_at}
                  </span>
                )}
              </div>
              {promise.payment.void_reason && (
                <div className="text-[var(--color-ink)]">
                  <span className="text-[var(--color-muted)]">Reason: </span>
                  <span className="font-medium">{promise.payment.void_reason}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {children}
      </div>
    </Card>
  )
}
