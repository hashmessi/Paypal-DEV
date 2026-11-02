import React, { useState } from 'react'
import { Button } from '../ui/Button'
import { SyntheticBadge } from './TrustBadge'
import { Clock } from 'lucide-react'

export interface ScenarioConsoleProps {
  onTriggerScenario: (
    scenario:
      | 'refurbished'
      | 'wrong_color'
      | 'corrected'
      | 'label_only'
      | 'late_eta'
      | 'duplicate_event'
      | 'price_change'
      | 'advance_clock'
  ) => Promise<unknown>
  paymentState?: string
  loading?: boolean
}

export const ScenarioConsole: React.FC<ScenarioConsoleProps> = ({
  onTriggerScenario,
  paymentState,
  loading = false,
}) => {
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [lastMessage, setLastMessage] = useState<string | null>(null)

  const isTerminal = paymentState === 'captured' || paymentState === 'voided' || paymentState === 'expired'

  const handleAction = async (
    key:
      | 'refurbished'
      | 'wrong_color'
      | 'corrected'
      | 'label_only'
      | 'late_eta'
      | 'duplicate_event'
      | 'price_change'
      | 'advance_clock',
    label: string
  ) => {
    setActiveAction(key)
    setLastMessage(null)
    try {
      await onTriggerScenario(key)
      setLastMessage(`Evidence dispatched: ${label}`)
    } catch (err) {
      setLastMessage(`Error: ${String(err)}`)
    } finally {
      setActiveAction(null)
    }
  }

  return (
    <div className="p-5 rounded-[var(--radius-card)] border-2 border-[var(--color-warn-line)] bg-white space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-[var(--color-warn-line)]/50 pb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-[14px] font-semibold uppercase tracking-[0.04em] text-[var(--color-warn)]">
            Scenario console
          </h3>
          <SyntheticBadge />
        </div>
        <p className="text-[12px] text-[var(--color-muted)]">
          Sends simulated fulfillment evidence. Does not execute payments.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'refurbished'}
          onClick={() => handleAction('refurbished', 'Item Condition Refurbished')}
          className="text-left justify-start"
          title={isTerminal ? 'Disabled: payment is in terminal state' : undefined}
        >
          Send refurbished item
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'wrong_color'}
          onClick={() => handleAction('wrong_color', 'Color Silver picked')}
          className="text-left justify-start"
          title={isTerminal ? 'Disabled: payment is in terminal state' : undefined}
        >
          Send wrong color
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || paymentState === 'captured'}
          loading={activeAction === 'corrected'}
          onClick={() => handleAction('corrected', 'Correct SKU + Carrier scan')}
          className="text-left justify-start font-semibold border-[var(--color-ok-line)] text-[var(--color-ok)] hover:bg-[var(--color-ok-soft)]"
          title={paymentState === 'captured' ? 'Disabled: already captured' : undefined}
        >
          Send correct item + carrier
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'label_only'}
          onClick={() => handleAction('label_only', 'Label created (no scan)')}
          className="text-left justify-start"
        >
          Send label only (no scan)
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'late_eta'}
          onClick={() => handleAction('late_eta', 'Carrier reported delayed ETA')}
          className="text-left justify-start"
        >
          Send late ETA
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'duplicate_event'}
          onClick={() => handleAction('duplicate_event', 'Replayed duplicate event')}
          className="text-left justify-start"
        >
          Replay duplicate event
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'price_change'}
          onClick={() => handleAction('price_change', 'Merchant raised price')}
          className="text-left justify-start"
        >
          Merchant changes price
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading}
          loading={activeAction === 'advance_clock'}
          onClick={() => handleAction('advance_clock', 'Clock offset +30 days')}
          icon={<Clock className="w-3.5 h-3.5" />}
          className="text-left justify-start text-[var(--color-warn)] border-[var(--color-warn-line)]"
        >
          Advance demo clock +30d
        </Button>
      </div>

      {lastMessage && (
        <div
          role="status"
          aria-live="polite"
          className="text-[12px] font-mono p-2 rounded bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)] flex items-center gap-2"
        >
          <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-ping" />
          <span>{lastMessage}</span>
        </div>
      )}
    </div>
  )
}
