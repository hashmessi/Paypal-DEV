import React from 'react'
import type { PillTone } from '../../lib/status'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: PillTone
  uppercase?: boolean
  icon?: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({
  tone = 'neutral',
  uppercase = false,
  icon,
  children,
  className = '',
  ...props
}) => {
  let toneClass = ''
  switch (tone) {
    case 'ok':
      toneClass = 'bg-[var(--color-ok-soft)] text-[var(--color-ok)] border-[var(--color-ok-line)]'
      break
    case 'warn':
      toneClass = 'bg-[var(--color-warn-soft)] text-[var(--color-warn)] border-[var(--color-warn-line)]'
      break
    case 'bad':
      toneClass = 'bg-[var(--color-bad-soft)] text-[var(--color-bad)] border-[var(--color-bad-line)]'
      break
    case 'info':
      toneClass = 'bg-[var(--color-info-soft)] text-[var(--color-info)] border-[var(--color-info-line)]'
      break
    case 'neutral':
    default:
      toneClass = 'bg-[var(--color-neutral-soft)] text-[var(--color-neutral)] border-[var(--color-neutral-line)]'
      break
  }

  const casing = uppercase ? 'uppercase tracking-[0.04em]' : ''

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[12px] font-semibold border ${toneClass} ${casing} ${className}`}
      {...props}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      {children}
    </span>
  )
}

