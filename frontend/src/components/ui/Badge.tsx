import React from 'react'
import type { PillTone } from '../../lib/status'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: PillTone
  uppercase?: boolean
  icon?: React.ReactNode
  dot?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  tone = 'neutral',
  uppercase = false,
  icon,
  dot = false,
  children,
  className = '',
  ...props
}) => {
  let toneClass = ''
  let dotClass = 'bg-[var(--color-neutral)]'

  switch (tone) {
    case 'ok':
      toneClass = 'bg-[var(--color-ok-soft)] text-[var(--color-ok)] border-[var(--color-ok-line)]'
      dotClass = 'bg-[var(--color-ok)]'
      break
    case 'warn':
      toneClass = 'bg-[var(--color-warn-soft)] text-[var(--color-warn)] border-[var(--color-warn-line)]'
      dotClass = 'bg-[var(--color-warn)]'
      break
    case 'bad':
      toneClass = 'bg-[var(--color-bad-soft)] text-[var(--color-bad)] border-[var(--color-bad-line)]'
      dotClass = 'bg-[var(--color-bad)]'
      break
    case 'info':
      toneClass = 'bg-[var(--color-info-soft)] text-[var(--color-info)] border-[var(--color-info-line)]'
      dotClass = 'bg-[var(--color-info)]'
      break
    case 'neutral':
    default:
      toneClass = 'bg-[var(--color-neutral-soft)] text-[var(--color-neutral)] border-[var(--color-neutral-line)]'
      dotClass = 'bg-[var(--color-neutral)]'
      break
  }

  const casing = uppercase ? 'uppercase tracking-[0.04em]' : ''

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 h-6 shrink-0 rounded-full whitespace-nowrap text-[12px] font-semibold border ${toneClass} ${casing} transition-colors ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotClass}`} aria-hidden="true" />}
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      {children}
    </span>
  )
}

