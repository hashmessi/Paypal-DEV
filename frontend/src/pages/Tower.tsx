import React, { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { useTower } from '../queries/useTower'
import { PageHeader } from '../components/ui/PageHeader'
import { StatCard } from '../components/ui/StatCard'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { AuthorizationPill, GatePill } from '../components/domain/StatusPill'
import { SyntheticBadge } from '../components/domain/TrustBadge'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { Skeleton } from '../components/ui/Skeleton'
import { formatMinor } from '../lib/money'
import { relativeTime, countdown } from '../lib/time'
import type { PurchasePromise } from '../types/api'

// AG Grid Community imports
import { AllCommunityModule, ModuleRegistry, themeQuartz, type ColDef, type ICellRendererParams } from 'ag-grid-community'
import { AgGridReact } from 'ag-grid-react'

import {
  RotateCw,
  Plus,
  AlertOctagon,
  ArrowRight,
  CheckCircle2,
  Activity,
  ShieldCheck,
  Lock,
} from 'lucide-react'

// Register AG Grid modules once
ModuleRegistry.registerModules([AllCommunityModule])

export const TowerPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isDriftFilter = searchParams.get('filter') === 'drift'

  const {
    data: towerData,
    isLoading,
    refetch,
    runDemoScenario,
    isRunningDemo,
    voidAuthorization,
    reconcile,
  } = useTower()

  const [voidPromiseId, setVoidPromiseId] = useState<string | null>(null)
  const [reconcilingId, setReconcilingId] = useState<string | null>(null)

  // Configure AG Grid quartz theme parameters matching UI-SPEC
  const gridTheme = useMemo(() => {
    return themeQuartz.withParams({
      backgroundColor: 'var(--color-surface)',
      headerBackgroundColor: 'var(--color-inset)',
      borderColor: 'var(--color-line)',
      accentColor: 'var(--color-accent)',
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      headerFontSize: 12,
      headerFontWeight: 600,
      wrapperBorderRadius: 12,
      rowHeight: 56,
      headerHeight: 44,
    })
  }, [])

  // Secondary columns only earn their width on large screens; below that the grid fits the rest.
  const [isWide, setIsWide] = useState(() => window.matchMedia('(min-width: 1536px)').matches)
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1536px)')
    const onChange = (e: MediaQueryListEvent) => setIsWide(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  const kpis = towerData?.kpis || {
    active_promises: 0,
    verified_outcomes_pct: 100,
    review_required: 0,
    authorized_not_captured_cents: 0,
    authorized_not_captured_count: 0,
  }

  const allPromises = towerData?.promises || []
  const displayedPromises = isDriftFilter
    ? allPromises.filter(
        (p) => p.gate_decision?.outcome === 'DRIFT' || p.gate_decision?.outcome === 'HOLD'
      )
    : allPromises

  const recentPromises = allPromises.slice(0, 4)
  // A percentage is only meaningful once at least one promise has a gate decision.
  const hasDecisions = allPromises.some((p) => p.gate_decision && p.gate_decision.outcome !== 'none')
  const needsAttention = allPromises.filter(
    (p) => p.gate_decision?.outcome === 'DRIFT' || p.gate_decision?.outcome === 'HOLD'
  )

  const handleVoid = async (reason?: string) => {
    if (!voidPromiseId || !reason) return
    await voidAuthorization({ id: voidPromiseId, reason })
    setVoidPromiseId(null)
  }

  const handleReconcile = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    setReconcilingId(id)
    try {
      await reconcile(id)
    } finally {
      setReconcilingId(null)
    }
  }

  // AG Grid Column Definitions
  const columnDefs: ColDef<PurchasePromise>[] = [
    {
      headerName: 'Promise',
      field: 'ref',
      width: 130,
      minWidth: 120,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        return (
          <span className="font-mono font-semibold text-[var(--color-accent)] hover:underline cursor-pointer whitespace-nowrap">
            {params.data.ref}
          </span>
        )
      },
    },
    {
      headerName: 'Product',
      flex: 2,
      minWidth: 200,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        const p = params.data
        return (
          <div className="min-w-0 py-1 leading-snug">
            <p className="font-semibold text-[var(--color-ink)] truncate">{p.product_snapshot.title}</p>
            <p className="text-[12px] text-[var(--color-muted)] truncate">
              {p.constraints.variant_color} · {p.constraints.condition}
            </p>
          </div>
        )
      },
    },
    {
      headerName: 'Amount',
      field: 'payment.amount_cents',
      width: 110,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        return (
          <span className="tabular-nums font-semibold text-[var(--color-ink)]">
            {formatMinor(params.data.payment.amount_cents)}
          </span>
        )
      },
    },
    {
      headerName: 'Authorization',
      flex: 1,
      minWidth: 180,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        return <AuthorizationPill state={params.data.payment.state} />
      },
    },
    {
      headerName: 'Gate',
      flex: 1,
      minWidth: 200,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        return (
          <GatePill
            outcome={params.data.gate_decision?.outcome}
            findings={params.data.gate_decision?.findings}
          />
        )
      },
    },
    {
      headerName: 'Auth expiry',
      width: 130,
      sort: 'asc',
      comparator: (a: string, b: string) => new Date(a).getTime() - new Date(b).getTime(),
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        const cd = countdown(params.data.payment.expiration_time)
        let tone = 'text-[var(--color-muted)]'
        if (cd.isExpired) tone = 'text-[var(--color-bad)] font-semibold'
        else if (cd.isExpiringSoon) tone = 'text-[var(--color-warn)] font-semibold'
        return <span className={`font-mono text-[12px] ${tone}`}>{cd.text}</span>
      },
    },
    {
      headerName: 'Evidence',
      width: 140,
      hide: !isWide,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        const count = params.data.evidence_events.length
        return (
          <div className="flex items-center gap-1.5">
            <span className="font-mono text-[12px]">{count}</span>
            <SyntheticBadge />
          </div>
        )
      },
    },
    {
      headerName: 'Updated',
      width: 120,
      hide: !isWide,
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        return (
          <span className="text-[12px] text-[var(--color-muted)]">
            {relativeTime(params.data.updated_at)}
          </span>
        )
      },
    },
    {
      headerName: 'Actions',
      width: 190,
      sortable: false,
      pinned: 'right',
      cellRenderer: (params: ICellRendererParams<PurchasePromise>) => {
        if (!params.data) return null
        const p = params.data
        const isVoided = p.payment.state === 'voided'
        return (
          <div className="flex items-center gap-1.5 py-1" onClick={(e) => e.stopPropagation()}>
            <Button
              size="sm"
              variant="secondary"
              loading={reconcilingId === p.id}
              onClick={(e) => handleReconcile(e, p.id)}
              className="text-[12px] h-8 px-2.5"
            >
              Reconcile
            </Button>
            <Button
              size="sm"
              variant="danger"
              disabled={isVoided}
              onClick={(e) => {
                e.stopPropagation()
                setVoidPromiseId(p.id)
              }}
              className="text-[12px] h-8 px-2.5"
            >
              Void…
            </Button>
          </div>
        )
      },
    },
  ]

  const activeVoidPromise = allPromises.find((p) => p.id === voidPromiseId)

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="COMMERCE ACCOUNTABILITY"
        title="Control tower"
        description="Unified risk management & fulfillment verification oversight. Real-time monitoring of agent authorizations and invariant drift."
        actions={
          <div className="flex items-center gap-2.5">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => refetch()}
              icon={<RotateCw className="w-4 h-4" />}
            >
              Refresh data
            </Button>
            <Button
              variant="primary"
              size="sm"
              loading={isRunningDemo}
              onClick={async () => {
                const res = await runDemoScenario()
                navigate(`/receipts/${res.purchase_id}`)
              }}
              icon={<Plus className="w-4 h-4" />}
            >
              Run demo scenario
            </Button>
          </div>
        }
      />

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatCard
          label="Active promises"
          value={kpis.active_promises}
          caption="In-flight authorizations"
          icon={<Activity className="w-4 h-4 text-[var(--color-accent)]" />}
        />
        <StatCard
          label="Verified outcomes"
          value={hasDecisions ? `${kpis.verified_outcomes_pct}%` : '—'}
          caption="Captured upon proof"
          tone={hasDecisions ? 'ok' : 'default'}
          icon={<ShieldCheck className="w-4 h-4 text-[var(--color-ok)]" />}
        />
        <StatCard
          label="Review required"
          value={kpis.review_required}
          caption="Open capture holds"
          tone={kpis.review_required > 0 ? 'bad' : 'default'}
          icon={<AlertOctagon className="w-4 h-4 text-[var(--color-bad)]" />}
        />
        <StatCard
          label="Authorized · not captured"
          value={formatMinor(kpis.authorized_not_captured_cents)}
          caption={`${kpis.authorized_not_captured_count} open holds`}
          tone={kpis.authorized_not_captured_count > 0 ? 'warn' : 'default'}
          icon={<Lock className="w-4 h-4 text-[var(--color-warn)]" />}
        />
        <StatCard
          label="$ protected"
          value={formatMinor(kpis.loss_avoided_cents ?? 0)}
          caption={kpis.loss_avoided_simulated ? 'Loss avoided · simulated' : 'Loss avoided vs naive agent'}
          tone={(kpis.loss_avoided_cents ?? 0) > 0 ? 'ok' : 'default'}
          icon={<ShieldCheck className="w-4 h-4 text-[var(--color-ok)]" />}
        />
      </div>

      {/* Two Auxiliary Panels: Recent promises + Needs attention */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: Recent promises */}
        <Card
          title="Recent promises"
          subtitle="Last 4 buyer commitments"
          action={
            <button
              type="button"
              onClick={() => navigate('/receipts')}
              className="text-[14px] text-[var(--color-accent)] font-semibold hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="w-3.5 h-3.5" />
            </button>
          }
        >
          <div className="divide-y divide-[var(--color-line)] text-[14px]">
            {recentPromises.length === 0 ? (
              <p className="text-[var(--color-muted)] py-4 text-center">No promises recorded yet.</p>
            ) : (
              recentPromises.map((p) => (
                <Link
                  key={p.id}
                  to={`/receipts/${p.id}`}
                  className="py-3 flex items-center justify-between hover:bg-[var(--color-inset)] px-2 rounded transition-colors"
                >
                  <div className="min-w-0 flex-1 mr-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-[var(--color-accent)] text-[12px] whitespace-nowrap shrink-0">
                        {p.ref}
                      </span>
                      <span className="font-semibold text-[var(--color-ink)] truncate">
                        {p.product_snapshot.title}
                      </span>
                    </div>
                    <p className="text-[12px] text-[var(--color-muted)] mt-0.5">
                      {relativeTime(p.created_at)} · {formatMinor(p.payment.amount_cents)} USD
                    </p>
                  </div>
                  <AuthorizationPill state={p.payment.state} className="shrink-0" />
                </Link>
              ))
            )}
          </div>
        </Card>

        {/* Panel 2: Needs attention */}
        <Card
          title="Needs attention"
          subtitle="Open drift mismatches and carrier holds"
          action={
            <button
              type="button"
              onClick={() => navigate('/tower?filter=drift')}
              className={`text-[14px] font-semibold hover:underline flex items-center gap-1 ${needsAttention.length > 0 ? 'text-[var(--color-bad)]' : 'text-[var(--color-accent)]'}`}
            >
              Open drift queue ({needsAttention.length}) <ArrowRight className="w-3.5 h-3.5" />
            </button>
          }
        >
          <div className="divide-y divide-[var(--color-line)] text-[14px]">
            {needsAttention.length === 0 ? (
              <div className="py-6 text-center text-[var(--color-muted)]">
                <CheckCircle2 className="w-5 h-5 mx-auto mb-1 text-[var(--color-ok)]" />
                <p>All authorizations currently match fulfillment evidence.</p>
              </div>
            ) : (
              needsAttention.map((p) => {
                const finding = p.gate_decision?.findings[0]
                return (
                  <Link
                    key={p.id}
                    to={`/tower/cases/${p.id}`}
                    className="py-3 flex items-center justify-between hover:bg-[var(--color-bad-soft)]/20 px-2 rounded transition-colors"
                  >
                    <div className="min-w-0 flex-1 mr-3 flex items-start gap-2.5">
                      <div className="p-1.5 rounded bg-[var(--color-bad-soft)] text-[var(--color-bad)] shrink-0 mt-0.5">
                        <AlertOctagon className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-semibold text-[var(--color-bad)] truncate">
                          {finding?.title || 'Fulfillment mismatch'}
                        </p>
                        <p className="text-[12px] text-[var(--color-muted)] mt-0.5 truncate">
                          {p.ref} · {p.product_snapshot.title} · {formatMinor(p.payment.amount_cents)} USD
                        </p>
                      </div>
                    </div>
                    <span className="shrink-0 text-[12px] font-semibold text-[var(--color-bad)]">Resolve</span>
                  </Link>
                )
              })
            )}
          </div>
        </Card>
      </div>

      {/* Full-width AG Grid Community Control Tower Table */}
      <Card
        padding="none"
        title="Commerce invariant control grid"
        subtitle={
          isDriftFilter
            ? 'Filtered by: Open drift & review holds'
            : 'All active and settled agent commerce commitments'
        }
        action={
          isDriftFilter ? (
            <Button size="sm" variant="secondary" onClick={() => navigate('/tower')}>
              Clear filter
            </Button>
          ) : undefined
        }
      >
        <div style={{ minHeight: 220, width: '100%' }}>
          <AgGridReact
            theme={gridTheme}
            domLayout="autoHeight"
            rowData={displayedPromises}
            columnDefs={columnDefs}
            defaultColDef={{
              resizable: true,
              sortable: true,
              cellClass: 'flex items-center',
            }}
            pagination={false}
            rowSelection="single"
            onRowClicked={(e) => {
              if (e.data) {
                if (e.data.gate_decision?.outcome === 'DRIFT') {
                  navigate(`/tower/cases/${e.data.id}`)
                } else {
                  navigate(`/receipts/${e.data.id}`)
                }
              }
            }}
            overlayNoRowsTemplate="<div class='p-8 text-center text-gray-500'>No commitments match the current view.</div>"
          />
        </div>
      </Card>

      {/* Void Dialog */}
      <ConfirmDialog
        isOpen={!!voidPromiseId}
        title="Void authorization"
        body={
          <p>
            This releases the{' '}
            <strong>
              {activeVoidPromise ? formatMinor(activeVoidPromise.payment.amount_cents) : ''}
            </strong>{' '}
            hold on the buyer's PayPal account. A voided authorization can never be captured. This cannot be undone.
          </p>
        }
        confirmLabel="Void authorization"
        cancelLabel="Keep authorization"
        destructive={true}
        requireReason={true}
        onConfirm={handleVoid}
        onClose={() => setVoidPromiseId(null)}
      />
    </div>
  )
}
