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
    ? 'border-[var(--color-bad-line)] bg-[var(--color-bad-soft)]/50 shadow-2xs ring-1 ring-[var(--color-bad-line)]/50'
    : 'border-[var(--color-line)] bg-white hover:bg-[var(--color-inset)]/50 shadow-2xs'

  return (
    <div className={`rounded-xl border transition-all duration-150 ${borderClass}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 text-left focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] cursor-pointer"
        aria-expanded={expanded}
      >
        <div className="flex items-center gap-3.5 min-w-0">
          <span
            className={`w-7 h-7 rounded-full flex items-center justify-center text-[12px] font-bold font-mono shrink-0 shadow-2xs ${
              isDivergence
                ? 'bg-[var(--color-bad)] text-white'
                : 'bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)]'
            }`}
          >
            {step.n}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[14px] font-bold text-[var(--color-ink)] tracking-tight">{step.title}</span>
              {isDivergence && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-[0.04em] px-2 py-0.5 rounded-full bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)]">
                  <AlertOctagon className="w-3 h-3" /> Divergence Detected
                </span>
              )}
            </div>
            <p className="text-[12px] text-[var(--color-muted)] mt-0.5">
              <span className="font-medium text-[var(--color-ink)]/70">{step.source}</span> · <span className="font-mono">{formatTimeOnly(step.occurred_at)}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 ml-3">
          {step.hash && <HashChip value={step.hash} kind="sha" />}
          {step.ids && step.ids.length > 0 && (
            <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[var(--color-inset)] border border-[var(--color-line)] text-[var(--color-muted)] hidden sm:inline-block">
              {step.ids[0]}
            </span>
          )}
          <span className="text-[var(--color-muted)] p-1 rounded-md hover:bg-black/5">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pt-1 border-t border-[var(--color-line)] text-[14px] space-y-3 animate-in fade-in duration-100">
          {step.finding && (
            <div className="p-3.5 rounded-lg bg-[var(--color-bad-soft)] border border-[var(--color-bad-line)] text-[var(--color-bad)] space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-bold uppercase px-1.5 py-0.5 bg-white rounded border border-current">{step.finding.code}</span>
                <span className="font-bold text-[13px]">{step.finding.title}</span>
              </div>
              <p className="text-[13px] text-[var(--color-ink)] leading-relaxed pt-1">{step.finding.explanation}</p>
            </div>
          )}

          {step.details && (
            <pre className="p-3 rounded-lg bg-[var(--color-inset)] border border-[var(--color-line)] font-mono text-[12px] text-[var(--color-ink)] overflow-x-auto leading-relaxed shadow-2xs">
              {JSON.stringify(step.details, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
