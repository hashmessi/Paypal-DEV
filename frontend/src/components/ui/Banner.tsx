import React from 'react'
import { AlertCircle, AlertTriangle, CheckCircle, Info, X } from 'lucide-react'
import type { PillTone } from '../../lib/status'

export interface BannerProps {
  tone?: PillTone
  title?: string
  body: React.ReactNode
  action?: React.ReactNode
  onDismiss?: () => void
}

export const Banner: React.FC<BannerProps> = ({
  tone = 'warn',
  title,
  body,
  action,
  onDismiss,
}) => {
  let styleClass = ''
  let IconComponent = AlertTriangle

  switch (tone) {
    case 'ok':
      styleClass = 'bg-[var(--color-ok-soft)] text-[var(--color-ok)] border-[var(--color-ok-line)]'
      IconComponent = CheckCircle
      break
    case 'bad':
      styleClass = 'bg-[var(--color-bad-soft)] text-[var(--color-bad)] border-[var(--color-bad-line)]'
      IconComponent = AlertCircle
      break
    case 'info':
      styleClass = 'bg-[var(--color-info-soft)] text-[var(--color-info)] border-[var(--color-info-line)]'
      IconComponent = Info
      break
    case 'warn':
    default:
      styleClass = 'bg-[var(--color-warn-soft)] text-[var(--color-warn)] border-[var(--color-warn-line)]'
      IconComponent = AlertTriangle
      break
  }

  return (
    <div
      role="status"
      className={`w-full border-b px-6 py-3 flex items-center justify-between gap-4 text-[14px] ${styleClass}`}
    >
      <div className="flex items-center gap-2.5">
        <IconComponent className="w-4 h-4 shrink-0" aria-hidden="true" />
        <div>
          {title && <span className="font-semibold mr-2">{title}</span>}
          <span>{body}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {action}
        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="p-1 rounded hover:opacity-75 focus-visible:outline-2"
            aria-label="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

