import React from 'react'
import { Badge } from '../ui/Badge'
import { getTrustBadge } from '../../lib/status'
import type { TrustLevel } from '../../types/api'

export interface TrustBadgeProps {
  trust: TrustLevel
  className?: string
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({ trust, className }) => {
  const { label, tone, note } = getTrustBadge(trust)
  return (
    <Badge tone={tone} className={className}>
      <span>{label}</span>
      {note && <span className="opacity-75 text-[11px] font-normal ml-0.5">({note})</span>}
    </Badge>
  )
}

export interface SyntheticBadgeProps {
  className?: string
}

export const SyntheticBadge: React.FC<SyntheticBadgeProps> = ({ className }) => {
  return (
    <Badge
      tone="warn"
      uppercase
      className={`font-mono text-[11px] font-normal border-dashed ${className || ''}`}
    >
      SYNTHETIC
    </Badge>
  )
}

