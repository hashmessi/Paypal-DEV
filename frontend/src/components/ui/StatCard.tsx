import React from 'react'
import { Card } from './Card'

export interface StatCardProps {
  label: string
  value: string | number
  caption?: string
  tone?: 'default' | 'warn' | 'bad' | 'ok'
  icon?: React.ReactNode
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, caption, tone = 'default', icon }) => {
  let valueColor = 'text-[var(--color-ink)]'
  let iconBg = 'bg-[var(--color-inset)] text-[var(--color-muted)]'

  if (tone === 'warn') {
    valueColor = 'text-[var(--color-warn)]'
    iconBg = 'bg-[var(--color-warn-soft)] text-[var(--color-warn)]'
  } else if (tone === 'bad') {
    valueColor = 'text-[var(--color-bad)]'
    iconBg = 'bg-[var(--color-bad-soft)] text-[var(--color-bad)]'
  } else if (tone === 'ok') {
    valueColor = 'text-[var(--color-ok)]'
    iconBg = 'bg-[var(--color-ok-soft)] text-[var(--color-ok)]'
  }

  return (
    <Card padding="md" tone={tone === 'default' ? 'default' : tone} hoverEffect>
      <div className="flex items-center justify-between gap-2">
        <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)] truncate">
          {label}
        </p>
        {icon && (
          <div className={`p-1.5 rounded-[var(--radius-control)] ${iconBg} shrink-0`}>
            {icon}
          </div>
        )}
      </div>
      <p className={`text-[28px] font-semibold tabular-nums mt-2 leading-tight ${valueColor}`}>{value}</p>
      {caption && (
        <div className="mt-2 pt-2 border-t border-[var(--color-line)]/50 flex items-center justify-between">
          <p className="text-[12px] text-[var(--color-muted)] truncate">{caption}</p>
        </div>
      )}
    </Card>
  )
}

