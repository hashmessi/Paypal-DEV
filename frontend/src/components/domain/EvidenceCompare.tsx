import React from 'react'

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
  expectedSource = 'Receipt v1',
  observedSource = 'Fulfillment adapter · EVT-0001',
  expectedLabel = 'BUYER-APPROVED',
  observedLabel = 'FULFILLMENT PICKED',
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
      <div className="p-4 rounded-[var(--radius-control)] border border-[var(--color-ok-line)] bg-[var(--color-ok-soft)]">
        <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-ok)]">
          {expectedLabel}
        </p>
        <p className="text-[18px] font-semibold text-[var(--color-ink)] mt-1">{expected}</p>
        <p className="text-[12px] text-[var(--color-muted)] mt-2">Source: {expectedSource}</p>
      </div>

      <div className="p-4 rounded-[var(--radius-control)] border border-[var(--color-bad-line)] bg-[var(--color-bad-soft)]">
        <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-bad)]">
          {observedLabel}
        </p>
        <p className="text-[18px] font-semibold text-[var(--color-bad)] mt-1">{observed}</p>
        <p className="text-[12px] text-[var(--color-muted)] mt-2">Source: {observedSource}</p>
      </div>
    </div>
  )
}

