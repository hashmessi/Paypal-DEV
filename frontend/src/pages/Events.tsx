import React, { useState } from 'react'
import { useNavigate } from 'react-router'
import { useEvents } from '../queries/useEvents'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { DataTable } from '../components/ui/DataTable'
import { Badge } from '../components/ui/Badge'
import { HashChip } from '../components/ui/HashChip'
import { Skeleton } from '../components/ui/Skeleton'
import { EmptyState } from '../components/ui/EmptyState'
import { formatTimeOnly } from '../lib/time'
import type { LedgerEventItem } from '../types/api'
import { Search } from 'lucide-react'

export const EventsPage: React.FC = () => {
  const navigate = useNavigate()
  const { data: events, isLoading } = useEvents()
  const [filter, setFilter] = useState('')

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64" />
      </div>
    )
  }

  const allEvents = events || []
  const filtered = allEvents.filter((e) => {
    const q = filter.toLowerCase()
    return (
      e.purchase_ref.toLowerCase().includes(q) ||
      e.type.toLowerCase().includes(q) ||
      e.source.toLowerCase().includes(q) ||
      e.actor.toLowerCase().includes(q)
    )
  })

  const columns = [
    {
      header: 'Seq',
      accessor: (row: LedgerEventItem) => <span className="font-mono text-[12px]">{row.seq}</span>,
      width: '60px',
    },
    {
      header: 'Time',
      accessor: (row: LedgerEventItem) => (
        <span className="font-mono text-[12px] text-[var(--color-muted)]">
          {formatTimeOnly(row.recorded_at)}
        </span>
      ),
      width: '90px',
    },
    {
      header: 'Event Type',
      accessor: (row: LedgerEventItem) => (
        <span className="font-mono text-[12px] font-semibold text-[var(--color-ink)]">
          {row.type}
        </span>
      ),
      width: '220px',
    },
    {
      header: 'Promise Ref',
      accessor: (row: LedgerEventItem) => (
        <span
          onClick={(e) => {
            e.stopPropagation()
            navigate(`/receipts/${row.purchase_id}`)
          }}
          className="font-mono font-semibold text-[var(--color-accent)] hover:underline cursor-pointer"
        >
          {row.purchase_ref}
        </span>
      ),
      width: '120px',
    },
    {
      header: 'Source / Actor',
      accessor: (row: LedgerEventItem) => (
        <div className="text-[13px]">
          <span className="text-[var(--color-ink)] font-semibold">{row.source}</span>
          <span className="text-[var(--color-muted)] text-[12px] ml-1.5">({row.actor})</span>
        </div>
      ),
    },
    {
      header: 'Payload Summary',
      accessor: (row: LedgerEventItem) => (
        <span className="text-[13px] text-[var(--color-ink)] truncate max-w-sm block">
          {row.payload_summary}
        </span>
      ),
    },
    {
      header: 'Hash / ID',
      accessor: (row: LedgerEventItem) => (
        <HashChip value={row.hash} kind={row.hash.startsWith('sha256') ? 'sha' : 'id'} />
      ),
      width: '140px',
    },
    {
      header: 'Status',
      accessor: (row: LedgerEventItem) => (
        <Badge tone={row.status_pill.tone}>{row.status_pill.label}</Badge>
      ),
      width: '100px',
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AUDIT TRAIL"
        title="Event history"
        description="Append-only cryptographic ledger recording every state change, buyer decision, and fulfillment transition across all purchases."
      />

      <Card padding="none">
        <div className="p-4 border-b border-[var(--color-line)] flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-3 text-[var(--color-muted)]" />
            <input
              type="text"
              placeholder="Filter by ref, event type, source..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full h-10 pl-9 pr-3 rounded-[var(--radius-control)] border border-[var(--color-line-strong)] text-[14px]"
            />
          </div>
          <span className="text-[13px] text-[var(--color-muted)]">{filtered.length} events</span>
        </div>

        <DataTable
          columns={columns}
          data={filtered}
          keyExtractor={(row) => `${row.purchase_id}-${row.seq}`}
          onRowClick={(row) => navigate(`/receipts/${row.purchase_id}`)}
          emptyState={
            <EmptyState
              title="No events recorded"
              body="Events appear as soon as a promise is created."
            />
          }
        />
      </Card>
    </div>
  )
}

