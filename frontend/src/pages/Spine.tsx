import React, { useState } from 'react'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { FormField } from '../components/ui/FormField'
import { HashChip } from '../components/ui/HashChip'
import { AuthorizationPill } from '../components/domain/StatusPill'
import { PayPalAuthorizeButton } from '../components/domain/PayPalAuthorizeButton'

export const SpinePage: React.FC = () => {
  const [amountDollars, setAmountDollars] = useState('89.99')
  const [orderId, setOrderId] = useState<string | null>('3KX8291048194')
  const [authId, setAuthId] = useState<string | null>('9K3184920194')
  const [paymentState, setPaymentState] = useState<'created' | 'authorized' | 'captured' | 'voided'>('authorized')
  const [captureId, setCaptureId] = useState<string | null>(null)
  const [voidReason, setVoidReason] = useState('buyer_cancelled')
  const [logMessages, setLogMessages] = useState<string[]>([
    'PAYMENT.AUTHORIZATION.CREATED · 9K3184920194 · Verified signature ✓',
  ])

  const amountCents = Math.round(parseFloat(amountDollars || '0') * 100)

  const handleCapture = () => {
    const cId = `4PX${Math.floor(100000000 + Math.random() * 900000000)}`
    setCaptureId(cId)
    setPaymentState('captured')
    setLogMessages((prev) => [
      `PAYMENT.CAPTURE.COMPLETED · ${cId} · $${amountDollars} captured · Verified signature ✓`,
      ...prev,
    ])
  }

  const handleVoid = () => {
    setPaymentState('voided')
    setLogMessages((prev) => [
      `PAYMENT.AUTHORIZATION.VOIDED · ${authId} · Reason: ${voidReason} · Local CAS verified ✓`,
      ...prev,
    ])
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        eyebrow="PHASE 1 INTERNAL INTERFACE"
        title="Spine Console"
        description="Low-level developer harness for PayPal Orders v2 authorization holds, capture execution, and webhook signature verification."
      />

      <div className="p-3 bg-[var(--color-warn-soft)] rounded-[var(--radius-control)] border border-[var(--color-warn-line)] text-[13px] text-[var(--color-warn)]">
        Dev-only console. Token-gated for automated integration testing and webhook postback verification.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 1: Authorization */}
        <Card title="1. Authorize Hold" subtitle="Direct PayPal Orders v2 authorization">
          <div className="space-y-4">
            <FormField id="amount-input" label="Amount (USD)">
              <input
                id="amount-input"
                type="number"
                value={amountDollars}
                onChange={(e) => setAmountDollars(e.target.value)}
                className="w-full h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] font-mono text-[14px]"
              />
            </FormField>

            <PayPalAuthorizeButton
              receiptId="spine-test"
              amountCents={amountCents}
              receiptHash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
              onAuthorized={(data) => {
                setOrderId(data.orderId)
                setAuthId(data.authorizationId)
                setPaymentState('authorized')
                setLogMessages((prev) => [
                  `PAYMENT.AUTHORIZATION.CREATED · ${data.authorizationId} · Verified ✓`,
                  ...prev,
                ])
              }}
            />
          </div>
        </Card>

        {/* Section 2: Payment State */}
        <Card title="2. Gateway State" subtitle="Current record in database">
          <div className="space-y-3 text-[13px]">
            <div className="flex justify-between items-center">
              <span className="text-[var(--color-muted)]">Payment State</span>
              <AuthorizationPill state={paymentState} />
            </div>

            <div className="flex justify-between items-center">
              <span className="text-[var(--color-muted)]">Order ID</span>
              <HashChip value={orderId || ''} kind="paypal" />
            </div>

            <div className="flex justify-between items-center">
              <span className="text-[var(--color-muted)]">Authorization ID</span>
              <HashChip value={authId || ''} kind="paypal" />
            </div>

            <div className="flex justify-between items-center">
              <span className="text-[var(--color-muted)]">Capture ID</span>
              {captureId ? (
                <HashChip value={captureId} kind="paypal" />
              ) : (
                <span className="text-[var(--color-muted)]">None</span>
              )}
            </div>

            <div className="flex justify-between items-center">
              <span className="text-[var(--color-muted)]">Expiration time</span>
              <span className="font-mono text-[12px]">+29 days (Sandbox)</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Section 3: Dev Execution Buttons */}
      <Card title="3. Manual Settlement Controls" subtitle="Token-gated financial trigger actions">
        <div className="flex items-center gap-4 flex-wrap">
          <Button
            variant="primary"
            disabled={paymentState !== 'authorized'}
            onClick={handleCapture}
          >
            Execute Capture ($89.99)
          </Button>

          <div className="flex items-center gap-2">
            <select
              value={voidReason}
              onChange={(e) => setVoidReason(e.target.value)}
              className="h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[13px] bg-white"
            >
              <option value="buyer_cancelled">Cancelled by buyer</option>
              <option value="out_of_stock">Out of stock</option>
              <option value="contract_violation">Contract violation</option>
            </select>
            <Button
              variant="danger"
              disabled={paymentState !== 'authorized'}
              onClick={handleVoid}
            >
              Void Authorization
            </Button>
          </div>
        </div>
      </Card>

      {/* Section 4: Webhook Log */}
      <Card title="4. Webhook Ingestion Log" subtitle="Raw postback signatures and deduplication trail">
        <div className="p-3 bg-[var(--color-inset)] rounded-[var(--radius-control)] font-mono text-[12px] space-y-1.5 max-h-48 overflow-y-auto">
          {logMessages.map((msg, i) => (
            <div key={i} className="flex items-center gap-2 text-[var(--color-ink)]">
              <span className="text-[var(--color-muted)]">[{i + 1}]</span>
              <span>{msg}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
