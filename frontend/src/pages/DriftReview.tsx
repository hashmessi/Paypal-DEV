import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useReceipt } from '../queries/useReceipt'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { EvidenceCompare } from '../components/domain/EvidenceCompare'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { FindingBanner } from '../components/domain/FindingBanner'
import { SyntheticBadge } from '../components/domain/TrustBadge'
import { PromiseHeaderPill } from '../components/domain/StatusPill'
import { Skeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { formatMinor } from '../lib/money'
import {
  RotateCw,
  Trash2,
  ArrowLeft,
} from 'lucide-react'

export const DriftReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const {
    data: promise,
    isLoading,
    sendScenario,
    isScenarioSending,
    voidAuthorization,
  } = useReceipt(id)

  const [isVoidDialogOpen, setIsVoidDialogOpen] = useState(false)
  const [recheckMessage, setRecheckMessage] = useState<string | null>(null)
  const [isRechecking, setIsRechecking] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-64 lg:col-span-2" />
          <Skeleton className="h-64" />
        </div>
      </div>
    )
  }

  if (!promise) {
    return (
      <EmptyState
        title="Drift case not found"
        body="This promise case does not exist or has already been resolved."
        action={
          <Button variant="secondary" onClick={() => navigate('/tower')}>
            Back to Control tower
          </Button>
        }
      />
    )
  }

  const primaryFinding =
    promise.gate_decision?.findings && promise.gate_decision.findings.length > 0
      ? promise.gate_decision.findings[0]
      : {
          code: 'CONDITION_MISMATCH',
          invariant: 'product' as const,
          severity: 'DRIFT' as const,
          expected: 'New',
          observed: 'Refurbished',
          title: 'Product condition does not match buyer approval',
          explanation:
            'Fulfillment adapter recorded item picked from warehouse in Refurbished condition. Buyer contract froze Condition = New. Capture blocked to prevent financial loss.',
        }

  const handleSendCorrected = async () => {
    await sendScenario({ scenarioKey: 'corrected' })
    navigate(`/receipts/${promise.id}`)
  }

  const handleRecheck = async () => {
    setIsRechecking(true)
    setRecheckMessage(null)
    await new Promise((r) => setTimeout(r, 500))
    setIsRechecking(false)
    if (promise.gate_decision?.outcome === 'MATCH') {
      setRecheckMessage('MATCH: All constraints verified. Ready for capture.')
    } else {
      setRecheckMessage(`Unchanged: ${primaryFinding.code} still active. Capture remains blocked.`)
    }
  }

  const handleConfirmVoid = async (reason?: string) => {
    if (!reason) return
    await voidAuthorization({ reason })
    setIsVoidDialogOpen(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => navigate(`/receipts/${promise.id}`)}
          icon={<ArrowLeft className="w-3.5 h-3.5" />}
        >
          Back to Receipt
        </Button>
      </div>

      <PageHeader
        eyebrow={`EXCEPTION REVIEW · ${promise.ref}`}
        title="Promise drift review"
        description="Fulfillment mismatch held financial settlement. Review discrepancy, send correction, or execute operator void."
        status={
          <PromiseHeaderPill
            paymentState={promise.payment.state}
            gateOutcome={promise.gate_decision?.outcome}
          />
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (8 cols): Evidence Comparison & Findings */}
        <div className="lg:col-span-8 space-y-6">
          {/* Finding Banner */}
          <FindingBanner
            code={primaryFinding.code}
            title={primaryFinding.title}
            severity={primaryFinding.severity}
            explanation={primaryFinding.explanation}
          />

          {/* Evidence Comparison Cards */}
          <Card
            title="Evidence Comparison"
            subtitle="Comparing frozen receipt snapshot against ingested warehouse and tracking evidence"
          >
            <EvidenceCompare
              expected={String(primaryFinding.expected)}
              observed={String(primaryFinding.observed)}
              expectedSource="Promise Receipt v1"
              observedSource="Fulfillment adapter · EVT-0001"
            />
          </Card>

          {/* Policy Evaluation Matrix */}
          <Card title="Promise Drift Engine Evaluation" subtitle="Deterministic invariant policy matrix">
            <div className="divide-y divide-[var(--color-line)] text-[13px]">
              <div className="py-2.5 flex justify-between items-center font-semibold text-[11px] uppercase tracking-wider text-[var(--color-muted)]">
                <span>Rule</span>
                <span>Result</span>
                <span>Enforcement Action</span>
              </div>

              <div className="py-3 flex justify-between items-center">
                <span className="font-semibold text-[var(--color-ink)]">Product Identity & SKU</span>
                <span className="text-[var(--color-ok)] font-semibold">PASS</span>
                <span className="text-[var(--color-muted)]">None</span>
              </div>

              <div className="py-3 flex justify-between items-center bg-[var(--color-bad-soft)]/20 px-2 rounded">
                <div>
                  <p className="font-semibold text-[var(--color-bad)]">Condition Invariant</p>
                  <p className="text-[11px] text-[var(--color-muted)] font-mono">rules.condition</p>
                </div>
                <span className="text-[var(--color-bad)] font-semibold uppercase">DRIFT</span>
                <span className="font-semibold text-[var(--color-bad)]">HOLD_CAPTURE</span>
              </div>

              <div className="py-3 flex justify-between items-center">
                <span className="font-semibold text-[var(--color-ink)]">Spending Limit Invariant</span>
                <span className="text-[var(--color-ok)] font-semibold">PASS ({formatMinor(promise.payment.amount_cents)})</span>
                <span className="text-[var(--color-muted)]">None</span>
              </div>

              <div className="py-3 flex justify-between items-center">
                <span className="font-semibold text-[var(--color-ink)]">Carrier Acceptance Scan</span>
                <span className="text-[var(--color-warn)] font-semibold">PENDING</span>
                <span className="text-[var(--color-muted)]">Awaiting UPS scan</span>
              </div>

              <div className="py-3 flex justify-between items-center">
                <span className="font-semibold text-[var(--color-ink)]">Authorization Expiry Window</span>
                <span className="text-[var(--color-ok)] font-semibold">VALID</span>
                <span className="text-[var(--color-muted)]">Active</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-[var(--color-line)] p-3 rounded bg-[var(--color-inset)] flex items-center justify-between text-[12px]">
              <span className="font-semibold text-[var(--color-ink)]">Financial Control: Deterministic</span>
              <span className="text-[var(--color-muted)] italic">"No LLM response can override this rule."</span>
            </div>
          </Card>
        </div>

        {/* Right Column (4 cols): Available Operator Actions */}
        <div className="lg:col-span-4 space-y-6">
          <Card title="Available Actions" subtitle="Operator resolution controls">
            <div className="space-y-3 pt-2">
              <div className="p-3 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[12px] font-semibold text-[var(--color-ink)]">Simulate correction</span>
                  <SyntheticBadge />
                </div>
                <p className="text-[12px] text-[var(--color-muted)]">
                  Simulates warehouse scanning corrected New condition item and carrier physical acceptance.
                </p>
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full font-semibold border-[var(--color-ok-line)] text-[var(--color-ok)] hover:bg-[var(--color-ok-soft)]"
                  loading={isScenarioSending}
                  onClick={handleSendCorrected}
                >
                  Send corrected item
                </Button>
              </div>

              <div className="space-y-1 pt-1">
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full"
                  loading={isRechecking}
                  onClick={handleRecheck}
                  icon={<RotateCw className="w-3.5 h-3.5" />}
                >
                  Re-run promise checks
                </Button>

                {recheckMessage && (
                  <p role="status" className="text-[12px] font-mono p-2 rounded bg-[var(--color-inset)] text-[var(--color-ink)]">
                    {recheckMessage}
                  </p>
                )}
              </div>

              <div className="pt-2 border-t border-[var(--color-line)]">
                <Button
                  size="sm"
                  variant="danger"
                  className="w-full"
                  disabled={promise.payment.state === 'voided'}
                  onClick={() => setIsVoidDialogOpen(true)}
                  icon={<Trash2 className="w-3.5 h-3.5" />}
                >
                  {promise.payment.state === 'voided' ? 'Authorization is voided' : 'Void authorization…'}
                </Button>
              </div>

              <div className="p-3 rounded-[var(--radius-control)] bg-[var(--color-warn-soft)] text-[12px] text-[var(--color-warn)] leading-relaxed">
                Capture remains blocked until corrected evidence passes revalidation or the hold is voided.
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Void Dialog */}
      <ConfirmDialog
        isOpen={isVoidDialogOpen}
        title="Void authorization"
        body={
          <p>
            This releases the <strong>{formatMinor(promise.payment.amount_cents)}</strong> hold on the buyer's PayPal account.
            A voided authorization can never be captured. This cannot be undone.
          </p>
        }
        confirmLabel="Void authorization"
        cancelLabel="Keep authorization"
        destructive={true}
        requireReason={true}
        onConfirm={handleConfirmVoid}
        onClose={() => setIsVoidDialogOpen(false)}
      />
    </div>
  )
}
