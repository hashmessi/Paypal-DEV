import React from 'react'
import { OctagonAlert, AlertTriangle, Info, ShieldAlert } from 'lucide-react'

export interface FindingBannerProps {
  code: string
  title: string
  severity: 'DRIFT' | 'HOLD' | 'INFO'
  explanation: string
  className?: string
}

export const FindingBanner: React.FC<FindingBannerProps> = ({
  code,
  title,
  severity,
  explanation,
  className = '',
}) => {
  let containerClass = 'bg-[var(--color-bad-soft)] border-[var(--color-bad-line)] text-[var(--color-bad)] shadow-xs'
  let Icon = OctagonAlert
  let severityLabel = 'Critical Invariant Drift · Capture Blocked'

  if (severity === 'HOLD') {
    containerClass = 'bg-[var(--color-warn-soft)] border-[var(--color-warn-line)] text-[var(--color-warn)] shadow-xs'
    Icon = AlertTriangle
    severityLabel = 'Review Hold · Awaiting Carrier Verification'
  } else if (severity === 'INFO') {
    containerClass = 'bg-[var(--color-info-soft)] border-[var(--color-info-line)] text-[var(--color-info)] shadow-xs'
    Icon = Info
    severityLabel = 'Fulfillment Evidence Notice'
  }

  return (
    <div className={`p-5 rounded-2xl border ${containerClass} ${className} relative overflow-hidden`}>
      <div className="flex items-start gap-3.5">
        <div className="p-2.5 rounded-xl bg-white shadow-2xs shrink-0 mt-0.5 border border-current/20">
          <Icon className="w-5 h-5 text-current" aria-hidden="true" />
        </div>
        <div className="space-y-2 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[12px] px-2 py-0.5 rounded-md bg-white border border-current/30 font-bold shadow-2xs">
              {code}
            </span>
            <span className="text-[11px] font-bold uppercase tracking-[0.05em] flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" />
              {severityLabel}
            </span>
          </div>
          <h2 className="text-[17px] font-bold text-[var(--color-ink)] leading-snug">{title}</h2>
          <div className="pt-2.5 border-t border-current/15">
            <p className="text-[11px] font-bold uppercase tracking-[0.05em] text-[var(--color-muted)] mb-1">
              Deterministic Root Cause & Gate Analysis
            </p>
            <p className="text-[14px] text-[var(--color-ink)] leading-relaxed font-normal bg-white/80 p-3 rounded-lg border border-current/10">
              {explanation}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
