import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useReceipt } from '../queries/useReceipt'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { PageHeader } from '../components/ui/PageHeader'
import { HashChip } from '../components/ui/HashChip'
import { Badge } from '../components/ui/Badge'
import { DataTable } from '../components/ui/DataTable'
import { Skeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import {
  PromiseHeaderPill,
  AuthorizationPill,
  GatePill,
} from '../components/domain/StatusPill'
import { TrustBadge, SyntheticBadge } from '../components/domain/TrustBadge'
import { Timeline } from '../components/domain/Timeline'
import { TruthPanel } from '../components/domain/TruthPanel'
import { PromiseProgressionHUD } from '../components/domain/PromiseProgressionHUD'
import { ScenarioConsole } from '../components/domain/ScenarioConsole'
import { FindingBanner } from '../components/domain/FindingBanner'
import { Ap2MandateModal } from '../components/domain/Ap2MandateModal'
import { formatMinor } from '../lib/money'
import { formatTimeOnly, formatDateTime } from '../lib/time'
import { api } from '../lib/api'
import type { FulfillmentEvent, PaymentState } from '../types/api'
import {
  ShieldCheck,
  History,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Package,
  Palette,
  DollarSign,
  Store,
  Truck,
  FileCheck,
  Download,
  ExternalLink,
  FileCode,
} from 'lucide-react'

const NOTE_TONE = {
  ok: 'bg-[var(--color-ok-soft)] border-[var(--color-ok-line)] text-[var(--color-ok)]',
  warn: 'bg-[var(--color-warn-soft)] border-[var(--color-warn-line)] text-[var(--color-warn)]',
  bad: 'bg-[var(--color-bad-soft)] border-[var(--color-bad-line)] text-[var(--color-bad)]',
  neutral: 'bg-[var(--color-inset)] border-[var(--color-line)] text-[var(--color-muted)]',
} as const

const HELD = 'Authorized, not captured. Not an escrow service.'

const PAYMENT_NOTE: Record<PaymentState, { tone: keyof typeof NOTE_TONE; text: string }> = {
  created: { tone: 'neutral', text: 'Order created. Awaiting buyer approval.' },
  approved: { tone: 'neutral', text: 'Buyer approved. Awaiting authorization.' },
  authorized: { tone: 'warn', text: HELD },
  capturing: { tone: 'warn', text: HELD },
  capture_pending: { tone: 'warn', text: 'Capture submitted and pending at PayPal.' },
  captured: { tone: 'ok', text: 'Funds captured after fulfillment was verified against this receipt.' },
  voided: { tone: 'neutral', text: 'Authorization voided. No funds were captured.' },
  expired: { tone: 'bad', text: 'Authorization expired. Capture is no longer possible.' },
  failed: { tone: 'bad', text: 'Payment failed. No funds were captured.' },
}

export const ReceiptPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const {
    data: promise,
    isLoading,
    error,
    sendScenario,
    isScenarioSending,
    reconcile,
    isReconciling,
  } = useReceipt(id)

  const [integrityStatus, setIntegrityStatus] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [ap2Mandate, setAp2Mandate] = useState<Record<string, unknown> | null>(null)
  const [isAp2ModalOpen, setIsAp2ModalOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-8 w-32" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-96 lg:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  if (error || !promise) {
    return (
      <EmptyState
        title="Couldn't load this promise."
        body="The server didn't respond. Retry, or check that the sandbox server has finished waking up."
        action={
          <Button variant="primary" onClick={() => window.location.reload()}>
            Retry
          </Button>
        }
      />
    )
  }

  const handleVerifyIntegrity = async () => {
    if (!promise) return
    setIsVerifying(true)
    setIntegrityStatus(null)
    try {
      const res = await api.verifyIntegrity(promise.id)
      if (res.intact) {
        setIntegrityStatus(`✓ Chain intact · ${res.event_count} events verified`)
      } else {
        setIntegrityStatus(`✗ Chain broken at event #${res.broken_step || 1}`)
      }
    } catch {
      setIntegrityStatus('✗ Verification failed: could not reach ledger')
    } finally {
      setIsVerifying(false)
    }
  }

  const handleExportReceiptJson = async () => {
    if (!promise) return
    try {
      const json = await api.getReceiptJson(promise.id)
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(json, null, 2))
      const a = document.createElement('a')
      a.setAttribute('href', dataStr)
      a.setAttribute('download', `promiseloop_receipt_${promise.ref || promise.id}.json`)
      document.body.appendChild(a)
      a.click()
      a.remove()
    } catch (e) {
      console.error('Failed to export receipt json', e)
    }
  }

  const handleExportAp2Mandate = async () => {
    if (!promise) return
    try {
      const mandate = await api.getAp2Mandate(promise.id)
      setAp2Mandate(mandate)
      setIsAp2ModalOpen(true)
    } catch (e) {
      console.error('Failed to load AP2 mandate', e)
    }
  }

  const handleVerifyOffline = async () => {
    if (!promise) return
    try {
      const json = await api.getReceiptJson(promise.id)
      navigate('/verify', { state: { receiptJson: JSON.stringify(json, null, 2) } })
    } catch {
      navigate('/verify')
    }
  }

  const handleReconcile = async () => {
    await reconcile()
  }

  const evidenceColumns = [
    {
      header: '#',
      accessor: (row: FulfillmentEvent) => <span className="font-mono text-[12px]">{row.seq}</span>,
      width: '48px',
    },
    {
      header: 'Source',
      accessor: (row: FulfillmentEvent) => (
        <span className="font-semibold text-[var(--color-ink)]">{row.source}</span>
      ),
    },
    {
      header: 'Type',
      accessor: (row: FulfillmentEvent) => (
        <span className="font-mono text-[12px] text-[var(--color-muted)]">{row.event_type}</span>
      ),
    },
    {
      header: 'Trust badge',
      accessor: (row: FulfillmentEvent) => <TrustBadge trust={row.source_type} />,
    },
    {
      header: 'Synthetic',
      accessor: (row: FulfillmentEvent) => (row.synthetic ? <SyntheticBadge /> : null),
    },
    {
      header: 'Observed value',
      accessor: (row: FulfillmentEvent) => (
        <div className="flex items-center gap-2">
          <span className="text-[14px]">{row.status_display}</span>
          {row.diff_summary && (
            <span className="text-[12px] font-mono px-1.5 py-0.5 rounded bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)]">
              Expected: {row.diff_summary.expected}
            </span>
          )}
        </div>
      ),
    },
    {
      header: 'Time',
      accessor: (row: FulfillmentEvent) => (
        <span className="font-mono text-[12px] text-[var(--color-muted)]">
          {formatTimeOnly(row.occurred_at)}
        </span>
      ),
      width: '100px',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        eyebrow={`PURCHASE RECORD · VERSION ${promise.version}`}
        title="Promise receipt"
        description="Frozen constraints agreement protecting settlement hold. Money moves only upon deterministic fulfillment verification."
        status={
          <PromiseHeaderPill
            paymentState={promise.payment.state}
            gateOutcome={promise.gate_decision?.outcome}
          />
        }
        actions={
          <div className="flex items-center gap-2.5">
            {promise.gate_decision?.outcome === 'DRIFT' && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => navigate(`/tower/cases/${promise.id}`)}
                icon={<AlertTriangle className="w-4 h-4" />}
              >
                Open drift review
              </Button>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={handleVerifyOffline}
              icon={<ExternalLink className="w-4 h-4" />}
            >
              Verify offline
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => navigate(`/receipts/${promise.id}/replay`)}
              icon={<History className="w-4 h-4" />}
            >
              Open replay
            </Button>
          </div>
        }
      />

      {/* 6-Stage Promise Progression HUD */}
      <PromiseProgressionHUD promise={promise} />

      {/* Stale Terms Banner */}
      {promise.status === 'stale' && (
        <div className="p-4 rounded-[var(--radius-card)] bg-[var(--color-warn-soft)] border border-[var(--color-warn-line)] flex items-center justify-between text-[14px] text-[var(--color-warn)]">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>Stale · reapproval required. The merchant updated its checkout terms.</span>
          </div>
          <Button size="sm" variant="secondary" onClick={() => navigate('/shop')}>
            Review version N+1
          </Button>
        </div>
      )}

      {/* Main Two-Column View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Promise Receipt Card (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          <Card padding="none">
            {/* Receipt Card Header */}
            <div className="p-6 border-b border-[var(--color-line)] bg-white">
              <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
                <span className="font-mono text-[12px] font-semibold text-[var(--color-accent)] tracking-wider">
                  PROMISE RECEIPT · {promise.ref}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)] border border-[var(--color-accent-line)]">
                  <FileCheck className="w-3 h-3" /> RFC 8785 Sealed
                </span>
                <AuthorizationPill state={promise.payment.state} />
              </div>
              <h2 className="text-[18px] font-semibold text-[var(--color-ink)] leading-snug">
                {promise.product_snapshot.title}
              </h2>
              <p className="text-[12px] text-[var(--color-muted)] mt-1">
                Created {formatDateTime(promise.created_at)} · Demo Merchant A
              </p>
            </div>

            {/* Section 1: Original Buyer Instruction */}
            <div className="p-6 border-b border-[var(--color-line)] bg-[var(--color-canvas)]/30 space-y-2">
              <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
                ORIGINAL BUYER INSTRUCTION
              </p>
              <blockquote className="text-[14px] font-normal text-[var(--color-ink)] italic bg-white p-3 rounded-[var(--radius-control)] border border-[var(--color-line)]">
                "{promise.buyer_instruction}"
              </blockquote>
              <div className="flex items-center gap-2 pt-1">
                <Badge tone="info">AI extracted</Badge>
                <Badge tone="ok">Buyer confirmed</Badge>
              </div>
            </div>

            {/* Section 2: Frozen Purchase Constraints (2x3 Grid) */}
            <div className="p-6 border-b border-[var(--color-line)] space-y-3">
              <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
                FROZEN PURCHASE CONSTRAINTS (HASH-LOCKED)
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-[14px]">
                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><Package className="w-3.5 h-3.5 text-[var(--color-muted)]" /> Product</span>
                  </p>
                  <p className="font-semibold text-[var(--color-ink)] mt-1 break-words">
                    {promise.constraints.product_type}
                  </p>
                </div>

                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><Palette className="w-3.5 h-3.5 text-[var(--color-muted)]" /> Variant</span>
                  </p>
                  <p className="font-semibold text-[var(--color-ink)] mt-1">{promise.constraints.variant_color}</p>
                </div>

                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-ok)]" /> Condition</span>
                  </p>
                  <p className="font-semibold text-[var(--color-ok)] mt-1">{promise.constraints.condition}</p>
                </div>

                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5 text-[var(--color-muted)]" /> Max total</span>
                  </p>
                  <p className="font-semibold tabular-nums text-[var(--color-ink)] mt-1">
                    {formatMinor(promise.constraints.max_total_cents)} USD
                  </p>
                </div>

                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><Store className="w-3.5 h-3.5 text-[var(--color-muted)]" /> Merchant</span>
                  </p>
                  <p className="font-mono text-[12px] text-[var(--color-ink)] mt-1 truncate">
                    {promise.merchant_quote.seller_domain}
                  </p>
                </div>

                <div className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                  <p className="text-[12px] text-[var(--color-muted)] uppercase tracking-wider font-semibold">
                    <span className="inline-flex items-center gap-1.5"><Truck className="w-3.5 h-3.5 text-[var(--color-muted)]" /> Delivery limit</span>
                  </p>
                  <p className="font-semibold text-[var(--color-ink)] mt-1">
                    Within {promise.constraints.deadline_days} days
                  </p>
                </div>
              </div>
            </div>

            {/* Section 3: Gate Decision */}
            <div className="p-6 border-b border-[var(--color-line)] space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
                  GATE (LATEST DRIFT DECISION)
                </p>
                <GatePill outcome={promise.gate_decision?.outcome} findings={promise.gate_decision?.findings} />
              </div>

              {promise.gate_decision?.outcome === 'DRIFT' && promise.gate_decision.findings.length > 0 && (
                <FindingBanner
                  code={promise.gate_decision.findings[0].code}
                  title={promise.gate_decision.findings[0].title}
                  severity="DRIFT"
                  explanation={promise.gate_decision.findings[0].explanation}
                />
              )}

              {promise.gate_decision?.outcome === 'MATCH' && (
                <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-ok-soft)] border border-[var(--color-ok-line)] text-[var(--color-ok)] flex items-center gap-2.5">
                  <CheckCircle2 className="w-5 h-5 shrink-0" />
                  <span className="text-[14px] font-semibold">
                    Fulfillment verified against all frozen constraints. Settlement capture completed.
                  </span>
                </div>
              )}

              {(!promise.gate_decision || promise.gate_decision.outcome === 'none') && (
                <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] text-[var(--color-muted)] text-[14px]">
                  Awaiting fulfillment evidence from warehouse adapter and carrier tracking scan.
                </div>
              )}
            </div>

            {/* Section 4: Promise Lifecycle */}
            <div className="p-6 space-y-4">
              <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
                PROMISE LIFECYCLE
              </p>
              <Timeline steps={promise.lifecycle} />
            </div>
          </Card>
        </div>

        {/* Right Column: PayPal transaction Card (4 cols, 360px) */}
        <div className="lg:col-span-4 space-y-6">
          <TruthPanel promise={promise}>
            {/* State-dependent settlement note; the escrow disclaimer applies only while funds are held */}
            {(() => {
              const note = PAYMENT_NOTE[promise.payment.state]
              return (
                <div
                  className={`p-3 rounded-[var(--radius-control)] border text-[12px] leading-relaxed ${NOTE_TONE[note.tone]}`}
                >
                  {note.text}
                </div>
              )
            })()}

            {/* Evidence sources checklist */}
            <div className="p-3 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2 text-[12px]">
              <p className="font-semibold uppercase tracking-wider text-[var(--color-muted)] text-[12px]">
                Evidence sources
              </p>
              <div className="flex items-center justify-between">
                <span>Buyer instruction</span>
                <span className="font-semibold text-[var(--color-ok)]">Confirmed ✓</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Product snapshot</span>
                <span className="font-semibold text-[var(--color-ok)]">Stored ✓</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Merchant promise</span>
                <span className="font-semibold text-[var(--color-ok)]">Stored ✓</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Fulfillment events</span>
                {promise.gate_decision?.outcome === 'DRIFT' ? (
                  <span className="font-semibold text-[var(--color-bad)]">Mismatch ✕</span>
                ) : promise.payment.state === 'captured' ? (
                  <span className="font-semibold text-[var(--color-ok)]">Verified ✓</span>
                ) : (
                  <span className="font-semibold text-[var(--color-muted)]">Awaiting …</span>
                )}
              </div>
              {promise.payment.state === 'captured' && (
                <div className="flex items-center justify-between pt-1 border-t border-[var(--color-line)]">
                  <span>PayPal Orders v2 tracking</span>
                  <span className="font-semibold text-[var(--color-ok)]">Pushed ✓</span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="pt-2 flex items-center justify-between">
              <Button
                size="sm"
                variant="secondary"
                loading={isReconciling}
                onClick={handleReconcile}
                icon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Reconcile
              </Button>

              <Button
                size="sm"
                variant="secondary"
                onClick={() => navigate(`/receipts/${promise.id}/replay`)}
                icon={<History className="w-3.5 h-3.5" />}
              >
                Audit replay
              </Button>
            </div>
          </TruthPanel>

          {/* Receipt integrity Card */}
          <Card padding="md" title="Receipt integrity" subtitle="Snapshot verification">
            <div className="space-y-3 text-[14px]">
              <div className="flex items-center justify-between">
                <span className="text-[var(--color-muted)]">Content hash</span>
                <HashChip value={promise.receipt_hash} kind="sha" />
              </div>

              <div className="flex items-center justify-between text-[12px]">
                <span className="text-[var(--color-muted)]">PayPal custom_id</span>
                <span className="font-semibold text-[var(--color-ok)]">matches anchor ✓</span>
              </div>

              <p className="text-[12px] text-[var(--color-muted)] italic">
                The hash protects the snapshot, not external truth.
              </p>

              <div className="pt-2 space-y-2">
                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full"
                  loading={isVerifying}
                  onClick={handleVerifyIntegrity}
                  icon={<ShieldCheck className="w-4 h-4" />}
                >
                  Verify ledger integrity
                </Button>

                <Button
                  size="sm"
                  variant="secondary"
                  className="w-full"
                  onClick={handleVerifyOffline}
                  icon={<ExternalLink className="w-4 h-4" />}
                >
                  Verify offline in browser
                </Button>

                <div className="grid grid-cols-2 gap-2 pt-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleExportReceiptJson}
                    icon={<Download className="w-3.5 h-3.5" />}
                  >
                    Receipt JSON
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleExportAp2Mandate}
                    icon={<FileCode className="w-3.5 h-3.5" />}
                  >
                    AP2 Mandate
                  </Button>
                </div>

                {integrityStatus && (
                  <p
                    role="status"
                    className="text-[12px] font-semibold text-[var(--color-ok)] text-center mt-2"
                  >
                    {integrityStatus}
                  </p>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Full-width Evidence List */}
      <Card
        title="Fulfillment evidence feed"
        subtitle="Ingested events from merchant warehouse and carrier delivery networks"
      >
        <DataTable
          columns={evidenceColumns}
          data={promise.evidence_events}
          keyExtractor={(row) => row.id}
          emptyState={
            <div className="py-8 text-center text-[var(--color-muted)] text-[14px]">
              No fulfillment evidence ingested yet. Trigger simulated events below.
            </div>
          }
        />
      </Card>

      {/* Scenario Console · SYNTHETIC */}
      <ScenarioConsole
        onTriggerScenario={(scenarioKey) => sendScenario({ scenarioKey })}
        paymentState={promise.payment.state}
        loading={isScenarioSending}
      />

      <Ap2MandateModal
        isOpen={isAp2ModalOpen}
        onClose={() => setIsAp2ModalOpen(false)}
        mandate={ap2Mandate}
        purchaseRef={promise.ref || promise.id}
      />
    </div>
  )
}
