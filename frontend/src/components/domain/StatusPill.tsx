import React from 'react'
import { OctagonAlert } from 'lucide-react'
import { Badge } from '../ui/Badge'
import {
  getAuthorizationPill,
  getGatePill,
  getReceiptPill,
  getPromiseStateHeaderPill,
} from '../../lib/status'
import type { PaymentState, GateOutcome, ReceiptStatus, Finding } from '../../types/api'

export interface AuthorizationPillProps {
  state: PaymentState
  className?: string
}

export const AuthorizationPill: React.FC<AuthorizationPillProps> = ({ state, className }) => {
  const info = getAuthorizationPill(state)
  return (
    <Badge tone={info.tone} className={className}>
      {info.label}
    </Badge>
  )
}

export interface GatePillProps {
  outcome?: GateOutcome | null
  findings?: Finding[]
  className?: string
}

export const GatePill: React.FC<GatePillProps> = ({ outcome, findings, className }) => {
  const info = getGatePill(outcome, findings)
  const isDrift = outcome === 'DRIFT'

  return (
    <Badge
      tone={info.tone}
      icon={isDrift ? <OctagonAlert className="w-3.5 h-3.5" aria-hidden="true" /> : undefined}
      className={className}
    >
      <span>{info.label}</span>
      {info.code && isDrift && (
        <span className="font-mono text-[12px] opacity-75 ml-1">({info.code})</span>
      )}
    </Badge>
  )
}

export interface ReceiptPillProps {
  status: ReceiptStatus
  className?: string
}

export const ReceiptPill: React.FC<ReceiptPillProps> = ({ status, className }) => {
  const info = getReceiptPill(status)
  return (
    <Badge tone={info.tone} className={className}>
      {info.label}
    </Badge>
  )
}

export interface PromiseHeaderPillProps {
  paymentState: PaymentState
  gateOutcome?: GateOutcome
  className?: string
}

export const PromiseHeaderPill: React.FC<PromiseHeaderPillProps> = ({
  paymentState,
  gateOutcome,
  className,
}) => {
  const info = getPromiseStateHeaderPill(paymentState, gateOutcome)

  return (
    <Badge
      tone={info.tone}
      icon={info.icon === 'octagon-alert' ? <OctagonAlert className="w-3.5 h-3.5" aria-hidden="true" /> : undefined}
      className={className}
    >
      {info.label}
    </Badge>
  )
}

