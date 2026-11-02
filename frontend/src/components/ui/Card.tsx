import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  subtitle?: string
  action?: React.ReactNode
  tone?: 'default' | 'bad' | 'warn' | 'ok'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  tone = 'default',
  padding = 'lg',
  children,
  className = '',
  ...props
}) => {
  let borderClass = 'border-[var(--color-line)]'
  let bgClass = 'bg-[var(--color-surface)]'

  if (tone === 'bad') {
    borderClass = 'border-[var(--color-bad-line)]'
    bgClass = 'bg-[var(--color-surface)]'
  } else if (tone === 'warn') {
    borderClass = 'border-[var(--color-warn-line)]'
  } else if (tone === 'ok') {
    borderClass = 'border-[var(--color-ok-line)]'
  }

  const paddingClass =
    padding === 'none'
      ? 'p-0'
      : padding === 'sm'
        ? 'p-4'
        : padding === 'md'
          ? 'p-5'
          : 'p-6'

  return (
    <div
      className={`rounded-[var(--radius-card)] border ${borderClass} ${bgClass} shadow-[var(--shadow-card)] overflow-hidden ${className}`}
      {...props}
    >
      {(title || action || subtitle) && (
        <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-2">
          <div>
            {title && <h2 className="text-[18px] font-semibold text-[var(--color-ink)] leading-snug">{title}</h2>}
            {subtitle && <p className="text-[14px] text-[var(--color-muted)] mt-1">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={paddingClass}>{children}</div>
    </div>
  )
}

