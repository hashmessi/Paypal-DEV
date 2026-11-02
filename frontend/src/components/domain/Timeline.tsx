import React from 'react'
import { Check, X, Circle, Loader2 } from 'lucide-react'
import { formatTimeOnly } from '../../lib/time'
import type { LifecycleStepItem } from '../../types/api'

export interface TimelineProps {
  steps: LifecycleStepItem[]
  className?: string
}

export const Timeline: React.FC<TimelineProps> = ({ steps, className = '' }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {steps.map((step, idx) => {
        let icon = <Circle className="w-4 h-4 text-[var(--color-line-strong)]" />
        let titleColor = 'text-[var(--color-muted)]'

        if (step.state === 'done') {
          icon = (
            <div className="w-5 h-5 rounded-full bg-[var(--color-ok-soft)] text-[var(--color-ok)] border border-[var(--color-ok-line)] flex items-center justify-center shrink-0">
              <Check className="w-3.5 h-3.5" aria-hidden="true" />
            </div>
          )
          titleColor = 'text-[var(--color-ink)]'
        } else if (step.state === 'current') {
          icon = (
            <div className="w-5 h-5 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-accent)] border border-[var(--color-accent)] flex items-center justify-center shrink-0 ring-2 ring-[var(--color-accent-soft)]">
              <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
            </div>
          )
          titleColor = 'text-[var(--color-ink)] font-semibold'
        } else if (step.state === 'failed') {
          icon = (
            <div className="w-5 h-5 rounded-full bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)] flex items-center justify-center shrink-0">
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </div>
          )
          titleColor = 'text-[var(--color-bad)] font-semibold'
        } else {
          icon = (
            <div className="w-5 h-5 rounded-full bg-[var(--color-inset)] text-[var(--color-muted)] border border-[var(--color-line)] flex items-center justify-center shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-line-strong)]" />
            </div>
          )
        }

        return (
          <div key={step.id || idx} className="flex items-start gap-3 relative">
            {/* Connecting line */}
            {idx < steps.length - 1 && (
              <span
                className="absolute left-2.5 top-6 bottom-[-16px] w-[1px] bg-[var(--color-line)]"
                aria-hidden="true"
              />
            )}
            <div className="z-10 bg-white py-0.5">{icon}</div>
            <div className="flex-1 pb-1">
              <p className={`text-[14px] leading-snug ${titleColor}`}>{step.title}</p>
              <div className="flex items-center gap-2 text-[12px] text-[var(--color-muted)] mt-0.5">
                <span className="font-mono">{formatTimeOnly(step.time)}</span>
                <span>·</span>
                <span>{step.source}</span>
                {step.ref_id && (
                  <>
                    <span>·</span>
                    <span className="font-mono text-[11px] px-1 py-0.2 rounded bg-[var(--color-inset)] border border-[var(--color-line)]">
                      {step.ref_id}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

