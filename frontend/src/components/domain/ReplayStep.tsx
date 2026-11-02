import React, { useState } from 'react'
import { ChevronDown, ChevronRight, AlertOctagon } from 'lucide-react'
import { HashChip } from '../ui/HashChip'
import { formatTimeOnly } from '../../lib/time'
import type { ReplayAuditStep } from '../../types/api'

export interface ReplayStepProps {
  step: ReplayAuditStep
}

export const ReplayStep: React.FC<ReplayStepProps> = ({ step }) => {
  const [expanded, setExpanded] = useState(step.divergence)

  const isDivergence = step.divergence
  const borderClass = isDivergence
    ? 'border-[var(--color-bad-line)] bg-[var(--color-bad-soft)]/40'
    : 'border-[var(--color-line)] bg-white hover:bg-[var(--color-inset)]/50'

  return (
    <div className={`rounded-[var(--radius-control)] border transition-colors ${borderClass}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3.5 text-left focus-visible:outline-2"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3">
          <span
            className={`w-6 h-6 rounded-full flex items-center justify-center text-[12px] font-semibold font-mono shrink-0 ${
              isDivergence
                ? 'bg-[var(--color-bad)] text-white'
                : 'bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)]'
            }`}
          >
            {step.n}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[14px] font-semibold text-[var(--color-ink)]">{step.title}</span>
              {isDivergence && (
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.04em] px-2 py-0.5 rounded bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)]">
                  <AlertOctagon className="w-3 h-3" /> Divergence
                </span>
              )}
            </div>
            <p className="text-[12px] text-[var(--color-muted)] mt-0.5">
              <span>{step.source}</span> · <span className="font-mono">{formatTimeOnly(step.occurred_at)}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {step.hash && <HashChip value={step.hash} kind="sha" />}
          {step.ids && step.ids.length > 0 && (
            <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-[var(--color-inset)] border border-[var(--color-line)] text-[var(--color-muted)]">
              {step.ids[0]}
            </span>
          )}
          <span className="text-[var(--color-muted)]">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-[var(--color-line)] text-[13px] space-y-2">
          {step.finding && (
            <div className="p-3 rounded bg-[var(--color-bad-soft)] border border-[var(--color-bad-line)] text-[var(--color-bad)] space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-semibold uppercase">{step.finding.code}</span>
                <span className="font-semibold">{step.finding.title}</span>
              </div>
              <p className="text-[12px] text-[var(--color-ink)]">{step.finding.explanation}</p>
            </div>
          )}

          {step.details && (
            <pre className="p-3 rounded bg-[var(--color-inset)] border border-[var(--color-line)] font-mono text-[12px] text-[var(--color-ink)] overflow-x-auto leading-relaxed">
              {JSON.stringify(step.details, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

