import React from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import { Badge } from '../ui/Badge'

export interface EvidenceCompareProps {
  expected: string
  observed: string
  expectedSource?: string
  observedSource?: string
  expectedLabel?: string
  observedLabel?: string
}

export const EvidenceCompare: React.FC<EvidenceCompareProps> = ({
  expected,
  observed,
  expectedSource = 'Promise Receipt v1 · Hash-sealed',
  observedSource = 'Warehouse Fulfillment Adapter · EVT-0001',
  expectedLabel = 'BUYER-APPROVED MANDATE',
  observedLabel = 'OBSERVED FULFILLMENT EVIDENCE',
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
      {/* Expected / Buyer Approved Card */}
      <div className="p-4 rounded-xl border border-[var(--color-ok-line)] bg-[var(--color-ok-soft)] shadow-2xs space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-bold uppercase tracking-[0.05em] text-[var(--color-ok)] flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>{expectedLabel}</span>
          </p>
          <Badge tone="ok" className="bg-white">
            Invariant Truth
          </Badge>
        </div>
        <p className="text-[18px] font-bold text-[var(--color-ink)] leading-snug">{expected}</p>
        <div className="pt-2 border-t border-[var(--color-ok-line)]/50 text-[11px] text-[var(--color-muted)] font-mono truncate">
          Source: {expectedSource}
        </div>
      </div>

      {/* Observed / Mismatch Card */}
      <div className="p-4 rounded-xl border border-[var(--color-bad-line)] bg-[var(--color-bad-soft)] shadow-2xs space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-bold uppercase tracking-[0.05em] text-[var(--color-bad)] flex items-center gap-1.5">
            <XCircle className="w-3.5 h-3.5 shrink-0" />
            <span>{observedLabel}</span>
          </p>
          <Badge tone="bad" className="bg-white font-bold">
            DRIFT DETECTED
          </Badge>
        </div>
        <p className="text-[18px] font-bold text-[var(--color-bad)] leading-snug">{observed}</p>
        <div className="pt-2 border-t border-[var(--color-bad-line)]/50 text-[11px] text-[var(--color-muted)] font-mono truncate">
          Source: {observedSource}
        </div>
      </div>
    </div>
  )
}
