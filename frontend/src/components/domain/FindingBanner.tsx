import React from 'react'
import { OctagonAlert, AlertTriangle, Info } from 'lucide-react'

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
  let containerClass = 'bg-[var(--color-bad-soft)] border-[var(--color-bad-line)] text-[var(--color-bad)]'
  let Icon = OctagonAlert

  if (severity === 'HOLD') {
    containerClass = 'bg-[var(--color-warn-soft)] border-[var(--color-warn-line)] text-[var(--color-warn)]'
    Icon = AlertTriangle
  } else if (severity === 'INFO') {
    containerClass = 'bg-[var(--color-info-soft)] border-[var(--color-info-line)] text-[var(--color-info)]'
    Icon = Info
  }

  return (
    <div className={`p-5 rounded-[var(--radius-card)] border ${containerClass} ${className}`}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-[12px] px-2 py-0.5 rounded bg-white/70 border border-current font-semibold">
              {code}
            </span>
            <span className="text-[12px] font-semibold uppercase tracking-[0.04em]">
              {severity === 'DRIFT' ? 'Critical Mismatch' : 'Review Hold'}
            </span>
          </div>
          <h2 className="text-[18px] font-semibold leading-snug">{title}</h2>
          <div className="pt-2 border-t border-current/20">
            <p className="text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)] mb-1">
              Explanation (AI or template)
            </p>
            <p className="text-[14px] text-[var(--color-ink)] leading-relaxed">{explanation}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

