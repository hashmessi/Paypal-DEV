import React from 'react'
import { useProof } from '../queries/useProof'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { DataTable } from '../components/ui/DataTable'
import { Badge } from '../components/ui/Badge'
import { Skeleton } from '../components/ui/Skeleton'
import type { ProofScenario } from '../types/api'
import { Check } from 'lucide-react'

export const ProofPage: React.FC = () => {
  const { data, isLoading } = useProof()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    )
  }

  const metrics = data?.metrics || []
  const scenarios = data?.scenarios || []

  const scenarioColumns = [
    {
      header: 'ID',
      accessor: (row: ProofScenario) => <span className="font-mono text-[12px] font-semibold">{row.id}</span>,
      width: '100px',
    },
    {
      header: 'Scenario Description',
      accessor: (row: ProofScenario) => (
        <div>
          <p className="font-semibold text-[var(--color-ink)]">{row.name}</p>
          <p className="text-[12px] text-[var(--color-muted)]">{row.category}</p>
        </div>
      ),
    },
    {
      header: 'Expected Outcome',
      accessor: (row: ProofScenario) => (
        <span className="font-mono text-[12px] text-[var(--color-ink)]">{row.expected_outcome}</span>
      ),
    },
    {
      header: 'Actual Outcome',
      accessor: (row: ProofScenario) => (
        <span className="font-mono text-[12px] text-[var(--color-ink)]">{row.actual_outcome}</span>
      ),
    },
    {
      header: 'Finding Codes',
      accessor: (row: ProofScenario) =>
        row.finding_codes.length > 0 ? (
          <div className="flex gap-1 flex-wrap">
            {row.finding_codes.map((c) => (
              <span
                key={c}
                className="font-mono text-[12px] px-1.5 py-0.2 rounded bg-[var(--color-inset)] border border-[var(--color-line)] text-[var(--color-bad)] font-semibold"
              >
                {c}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-[12px] text-[var(--color-muted)]">—</span>
        ),
    },
    {
      header: 'Result',
      accessor: (row: ProofScenario) => (
        <Badge tone={row.passed ? 'ok' : 'bad'}>
          {row.passed ? 'PASS' : 'FAIL'}
        </Badge>
      ),
      width: '90px',
    },
  ]

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="EVIDENCE & VERIFICATION"
        title="Proof & technical metrics"
        description="Empirical benchmark suite measuring invariant drift precision, capture safety, and rule execution speed across labeled test scenarios."
      />

      {/* 6 Metric Cards with Numerator / Denominator Large */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((m, idx) => (
          <Card key={idx} padding="md" hoverEffect>
            <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
              {m.title}
            </p>
            <div className="flex items-baseline gap-1.5 my-2">
              <span className="text-[28px] font-semibold tabular-nums text-[var(--color-ink)]">
                {m.numerator}
              </span>
              <span className="text-[18px] text-[var(--color-muted)] font-normal">/</span>
              <span className="text-[18px] tabular-nums text-[var(--color-muted)] font-normal">
                {m.denominator}
              </span>
              {m.unit && <span className="text-[14px] text-[var(--color-muted)] font-semibold ml-1">{m.unit}</span>}
            </div>
            <p className="text-[14px] text-[var(--color-muted)] leading-relaxed">{m.definition}</p>
            <p className="text-[12px] font-mono text-[var(--color-muted)] mt-3 truncate">{m.source_run}</p>
          </Card>
        ))}
      </div>

      {/* Proves / Does Not Prove Two-Column Card */}
      <Card
        title="System boundaries & claims"
        subtitle="Clear, honest disclosure of technical proof capabilities"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-ok-soft)] border border-[var(--color-ok-line)] space-y-3">
            <h3 className="text-[14px] font-semibold uppercase tracking-[0.04em] text-[var(--color-ok)] flex items-center gap-1.5">
              <Check className="w-4 h-4" /> What PromiseLoop Proves
            </h3>
            <ul className="space-y-2 text-[14px] text-[var(--color-ink)]">
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-ok)] font-bold">✓</span>
                <span>
                  <strong>Zero unauthorized settlements:</strong> Funds are never captured if fulfillment evidence deviates from the frozen snapshot.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-ok)] font-bold">✓</span>
                <span>
                  <strong>Cryptographic snapshot freezing:</strong> The receipt is bound by canonical SHA-256 and anchored in the PayPal order <code className="font-mono">custom_id</code>.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-ok)] font-bold">✓</span>
                <span>
                  <strong>Tamper-evident audit ledger:</strong> All events append to a hash-chained sequence where unauthorized edits break verification.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[var(--color-ok)] font-bold">✓</span>
                <span>
                  <strong>Separation of concerns:</strong> The LLM suggests constraints; deterministic Python/TypeScript logic controls money movement.
                </span>
              </li>
            </ul>
          </div>

          <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-3">
            <h3 className="text-[14px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
              What PromiseLoop Does NOT Prove
            </h3>
            <ul className="space-y-2 text-[14px] text-[var(--color-muted)]">
              <li className="flex items-start gap-2">
                <span>✕</span>
                <span>
                  <strong>External physical truth:</strong> The engine verifies ingested evidence; it cannot verify whether warehouse workers committed physical barcode fraud.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span>✕</span>
                <span>
                  <strong>Real carrier network integration:</strong> Tracking events in this demo are simulated (SYNTHETIC) via standard adapter protocols.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span>✕</span>
                <span>
                  <strong>Escrow services:</strong> PromiseLoop does not hold deposits; it leverages native card network authorization hold lifecycles.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </Card>

      {/* Labeled Scenarios Table */}
      <Card
        padding="none"
        title="Automated acceptance scenarios (11 cases)"
        subtitle="Table-driven invariant test suite verifying all acceptance criteria"
      >
        <DataTable
          columns={scenarioColumns}
          data={scenarios}
          keyExtractor={(row) => row.id}
        />
      </Card>

      {/* Reference Links */}
      <div className="flex items-center justify-between text-[14px] text-[var(--color-muted)] pt-2 border-t border-[var(--color-line)]">
        <span>AP2 v0.2 Protocol Specification Alignment</span>
        <span>Apache 2.0 Open Source License</span>
      </div>
    </div>
  )
}
