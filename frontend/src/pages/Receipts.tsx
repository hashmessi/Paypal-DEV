import React, { useState } from 'react'
import { useNavigate } from 'react-router'
import { useTower } from '../queries/useTower'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { DataTable } from '../components/ui/DataTable'
import { AuthorizationPill, GatePill } from '../components/domain/StatusPill'
import { EmptyState } from '../components/ui/EmptyState'
import { Skeleton } from '../components/ui/Skeleton'
import { formatMinor } from '../lib/money'
import { relativeTime } from '../lib/time'
import type { PurchasePromise } from '../types/api'
import { Search, Plus } from 'lucide-react'

export const ReceiptsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: towerData, isLoading, runDemoScenario, isRunningDemo } = useTower()
  const [search, setSearch] = useState('')

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  const promises = towerData?.promises || []
  const filtered = promises.filter((p) => {
    const q = search.toLowerCase()
    return (
      p.ref.toLowerCase().includes(q) ||
      p.product_snapshot.title.toLowerCase().includes(q) ||
      p.buyer_instruction.toLowerCase().includes(q)
    )
  })

  const columns = [
    {
      header: 'Promise Ref',
      accessor: (row: PurchasePromise) => (
        <span className="font-mono font-semibold text-[var(--color-accent)] hover:underline whitespace-nowrap">
          {row.ref}
        </span>
      ),
      width: '130px',
    },
    {
      header: 'Product & Details',
      accessor: (row: PurchasePromise) => (
        <div>
          <p className="font-semibold text-[var(--color-ink)] truncate max-w-xs">{row.product_snapshot.title}</p>
          <p className="text-[12px] text-[var(--color-muted)]">
            {row.constraints.variant_color} · {row.constraints.condition}
          </p>
        </div>
      ),
    },
    {
      header: 'Amount',
      accessor: (row: PurchasePromise) => (
        <span className="tabular-nums font-semibold text-[var(--color-ink)]">
          {formatMinor(row.payment.amount_cents)} USD
        </span>
      ),
      width: '120px',
    },
    {
      header: 'Authorization',
      accessor: (row: PurchasePromise) => <AuthorizationPill state={row.payment.state} />,
      width: '170px',
    },
    {
      header: 'Gate',
      accessor: (row: PurchasePromise) => (
        <GatePill outcome={row.gate_decision?.outcome} findings={row.gate_decision?.findings} />
      ),
      width: '180px',
    },
    {
      header: 'Created',
      accessor: (row: PurchasePromise) => (
        <span className="text-[12px] text-[var(--color-muted)]">{relativeTime(row.created_at)}</span>
      ),
      width: '100px',
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="COMMERCE ACCOUNTABILITY"
        title="Promise receipts"
        description="Immutable registry of all buyer constraint agreements and their linked PayPal authorizations."
        actions={
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
        }
      />

      <Card padding="none">
        <div className="p-4 border-b border-[var(--color-line)] flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-3 text-[var(--color-muted)]" />
            <input
              type="text"
              placeholder="Search promises by ref, item..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-10 pl-9 pr-3 rounded-[var(--radius-control)] border border-[var(--color-line-strong)] text-[14px]"
            />
          </div>
          <span className="text-[14px] text-[var(--color-muted)]">{filtered.length} total</span>
        </div>

        <DataTable
          columns={columns}
          data={filtered}
          keyExtractor={(row) => row.id}
          onRowClick={(row) => navigate(`/receipts/${row.id}`)}
          emptyState={
            <EmptyState
              title="No promises yet"
              body="Run the demo scenario to create a receipt, an authorization and the first evidence."
              action={
                <Button variant="primary" onClick={() => runDemoScenario()}>
                  Run demo scenario
                </Button>
              }
            />
          }
        />
      </Card>
    </div>
  )
}
