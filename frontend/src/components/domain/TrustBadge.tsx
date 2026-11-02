import React from 'react'
import { Badge } from '../ui/Badge'
import { getTrustBadge } from '../../lib/status'
import type { TrustLevel } from '../../types/api'
import { ShieldCheck, Sparkles } from 'lucide-react'

export interface TrustBadgeProps {
  trust: TrustLevel
  className?: string
}

export const TrustBadge: React.FC<TrustBadgeProps> = ({ trust, className }) => {
  const { label, tone, note } = getTrustBadge(trust)
  const isHighTrust = trust === 'carrier' || trust === 'merchant_system'

  return (
    <Badge
      tone={tone}
      icon={isHighTrust ? <ShieldCheck className="w-3 h-3 text-current" /> : undefined}
      className={className}
    >
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
      tone="neutral"
      icon={<Sparkles className="w-3 h-3 opacity-60" />}
      className={`bg-white/80 border-dashed text-[11px] ${className || ''}`}
    >
      Synthetic
    </Badge>
  )
}
