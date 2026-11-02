import React from 'react'
import { Card } from './Card'

export interface StatCardProps {
  label: string
  value: string | number
  caption?: string
  tone?: 'default' | 'warn' | 'bad' | 'ok'
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, caption, tone = 'default' }) => {
  let valueColor = 'text-[var(--color-ink)]'
  if (tone === 'warn') valueColor = 'text-[var(--color-warn)]'
  if (tone === 'bad') valueColor = 'text-[var(--color-bad)]'
  if (tone === 'ok') valueColor = 'text-[var(--color-ok)]'

  return (
    <Card padding="md" tone={tone === 'default' ? 'default' : tone}>
      <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">{label}</p>
      <p className={`text-[28px] font-semibold tabular-nums mt-1 leading-tight ${valueColor}`}>{value}</p>
      {caption && <p className="text-[12px] text-[var(--color-muted)] mt-1">{caption}</p>}
    </Card>
  )
}

