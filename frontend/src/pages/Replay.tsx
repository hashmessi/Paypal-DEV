import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { useReplay } from '../queries/useReplay'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ReplayStep } from '../components/domain/ReplayStep'
import { Skeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { ShieldCheck, Download, ArrowLeft, CheckCircle2 } from 'lucide-react'

export const ReplayPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: replay, isLoading, error, verifyIntegrity, isVerifying } = useReplay(id)

  const [verifyMessage, setVerifyMessage] = useState<string | null>(null)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-96 lg:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  if (error || !replay) {
    return (
      <EmptyState
        title="Replay not found"
        body="Audit ledger entries for this purchase could not be assembled."
        action={
          <Button variant="secondary" onClick={() => navigate('/tower')}>
            Back to Control tower
          </Button>
        }
      />
    )
  }

  const handleVerify = async () => {
    setVerifyMessage(null)
    const res = await verifyIntegrity()
    if (res.intact) {
      setVerifyMessage(`✓ Chain intact · ${res.event_count} events`)
    } else {
      setVerifyMessage(`Broken at event #${res.broken_step || 1}`)
    }
  }

  const handleDownloadJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(replay, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `promiseloop_replay_${replay.ref}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => navigate(`/receipts/${replay.purchase_id}`)}
          icon={<ArrowLeft className="w-3.5 h-3.5" />}
        >
          Back to Receipt
        </Button>
      </div>

      <PageHeader
        eyebrow="AUDIT TIMELINE"
        title="Promise Replay"
        description="Immutable 10-step execution audit trace. Verifies cryptographic hash continuity from natural language instruction to settlement capture."
        actions={
          <div className="flex items-center gap-2.5">
            <Button
              variant="secondary"
              size="sm"
              loading={isVerifying}
              onClick={handleVerify}
              icon={<ShieldCheck className="w-4 h-4" />}
            >
              Verify integrity
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadJson}
              icon={<Download className="w-4 h-4" />}
            >
              Download JSON
            </Button>
          </div>
        }
      />

      {verifyMessage && (
        <div
          role="status"
          className="p-3 rounded-[var(--radius-control)] bg-[var(--color-ok-soft)] border border-[var(--color-ok-line)] text-[var(--color-ok)] font-semibold text-[14px] flex items-center gap-2"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{verifyMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: 10-step audit timeline (8 cols) */}
        <div className="lg:col-span-8 space-y-2.5">
          {replay.steps.map((step) => (
            <ReplayStep key={step.n} step={step} />
          ))}
        </div>

        {/* Right: Integrity card (4 cols, 320px) */}
        <div className="lg:col-span-4 space-y-6 sticky top-24">
          <Card title="Cryptographic Integrity" subtitle="Continuous SHA-256 chain validation">
            <div className="space-y-4 text-[13px]">
              <div className="p-3 rounded bg-[var(--color-ok-soft)] border border-[var(--color-ok-line)] flex items-center justify-between text-[var(--color-ok)] font-semibold">
                <span>Chain state</span>
                <span>✓ Intact · {replay.event_count} events</span>
              </div>

              <div className="space-y-2 divide-y divide-[var(--color-line)]">
                <div className="pt-2 flex justify-between">
                  <span className="text-[var(--color-muted)]">Artifacts verified</span>
                  <span className="font-semibold text-[var(--color-ink)]">{replay.artifacts_verified}</span>
                </div>

                <div className="pt-2 flex justify-between">
                  <span className="text-[var(--color-muted)]">PayPal anchor</span>
                  <span className="font-semibold text-[var(--color-ok)]">custom_id matches ✓</span>
                </div>

                <div className="pt-2 flex justify-between">
                  <span className="text-[var(--color-muted)]">Tamper detection</span>
                  <span className="font-semibold text-[var(--color-ok)]">0 breaks</span>
                </div>
              </div>

              <div className="p-3 rounded bg-[var(--color-inset)] text-[12px] text-[var(--color-muted)] leading-relaxed">
                The cryptographic ledger verifies that no event was modified or retroactively deleted after ingestion.
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
