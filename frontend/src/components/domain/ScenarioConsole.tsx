import React, { useState } from 'react'
import { Button } from '../ui/Button'
import { SyntheticBadge } from './TrustBadge'
import {
  Clock,
  PackageX,
  Palette,
  CheckCircle2,
  Tag,
  CalendarClock,
  CopyCheck,
  TrendingUp,
  Terminal,
  ShieldAlert,
} from 'lucide-react'

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
      | 'prompt_injection'
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
      | 'advance_clock'
      | 'prompt_injection',
    label: string
  ) => {
    setActiveAction(key)
    setLastMessage(null)
    try {
      await onTriggerScenario(key)
      setLastMessage(`Dispatched: ${label} → Promise Drift Engine re-evaluated gate.`)
    } catch (err) {
      setLastMessage(`Error: ${String(err)}`)
    } finally {
      setActiveAction(null)
    }
  }

  return (
    <div className="p-6 rounded-2xl border border-[var(--color-line)] bg-white shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-[var(--color-line)] pb-4">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="p-1.5 rounded-lg bg-[var(--color-warn-soft)] text-[var(--color-warn)] border border-[var(--color-warn-line)]">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-[14px] font-bold uppercase tracking-[0.04em] text-[var(--color-ink)]">
                Scenario fulfillment simulation console
              </h3>
              <SyntheticBadge />
            </div>
            <p className="text-[12px] text-[var(--color-muted)] mt-0.5">
              Injects realistic carrier & warehouse webhook events into the deterministic drift engine.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {/* Row 1: Drift & Adversarial Invariants */}
        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'refurbished'}
          onClick={() => handleAction('refurbished', 'Item Condition Refurbished (INV-01 Drift)')}
          icon={<PackageX className="w-3.5 h-3.5 text-[var(--color-bad)]" />}
          className="text-left justify-start h-10 px-3 hover:border-[var(--color-bad-line)] hover:bg-[var(--color-bad-soft)]/40"
          title={isTerminal ? 'Disabled: payment is in terminal state' : 'Inject condition mismatch (REFURBISHED)'}
        >
          <span className="truncate">Refurbished item</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'wrong_color'}
          onClick={() => handleAction('wrong_color', 'Color Silver Picked (INV-02 Drift)')}
          icon={<Palette className="w-3.5 h-3.5 text-[var(--color-bad)]" />}
          className="text-left justify-start h-10 px-3 hover:border-[var(--color-bad-line)] hover:bg-[var(--color-bad-soft)]/40"
          title={isTerminal ? 'Disabled: payment is in terminal state' : 'Inject color variant drift (SILVER)'}
        >
          <span className="truncate">Wrong color</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'prompt_injection'}
          onClick={() => handleAction('prompt_injection', 'Adversarial Prompt Injection in Tracking Note (Neutralized)')}
          icon={<ShieldAlert className="w-3.5 h-3.5 text-rose-600" />}
          className="text-left justify-start h-10 px-3 border-rose-200 hover:border-rose-400 hover:bg-rose-50/60"
          title={isTerminal ? 'Disabled: payment is in terminal state' : 'Inject adversarial prompt injection into carrier note'}
        >
          <span className="truncate font-medium text-rose-700">Prompt injection attack</span>
        </Button>

        {/* Row 2: In-Flight Holds & Quote Changes */}
        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'label_only'}
          onClick={() => handleAction('label_only', 'Label created, awaiting carrier scan (HOLD)')}
          icon={<Tag className="w-3.5 h-3.5 text-[var(--color-warn)]" />}
          className="text-left justify-start h-10 px-3 hover:border-[var(--color-warn-line)] hover:bg-[var(--color-warn-soft)]/40"
        >
          <span className="truncate">Label only (no scan)</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'late_eta'}
          onClick={() => handleAction('late_eta', 'Carrier reported delayed ETA past deadline (HOLD)')}
          icon={<CalendarClock className="w-3.5 h-3.5 text-[var(--color-warn)]" />}
          className="text-left justify-start h-10 px-3 hover:border-[var(--color-warn-line)] hover:bg-[var(--color-warn-soft)]/40"
        >
          <span className="truncate">Late ETA reported</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'price_change'}
          onClick={() => handleAction('price_change', 'Merchant quote price shifted (STALE terms)')}
          icon={<TrendingUp className="w-3.5 h-3.5 text-[var(--color-warn)]" />}
          className="text-left justify-start h-10 px-3 hover:border-[var(--color-warn-line)] hover:bg-[var(--color-warn-soft)]/40"
        >
          <span className="truncate">Merchant changes price</span>
        </Button>

        {/* Row 3: Resolution & Lifecycle Execution */}
        <Button
          size="sm"
          variant="secondary"
          disabled={loading || paymentState === 'captured'}
          loading={activeAction === 'corrected'}
          onClick={() => handleAction('corrected', 'Exact SKU + Carrier scan (Gate MATCH)')}
          icon={<CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-ok)]" />}
          className="text-left justify-start h-10 px-3 font-semibold border-[var(--color-ok-line)] text-[var(--color-ok)] hover:bg-[var(--color-ok-soft)]"
          title={paymentState === 'captured' ? 'Disabled: already captured' : 'Inject verified match'}
        >
          <span className="truncate">Correct item + Carrier</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading || isTerminal}
          loading={activeAction === 'duplicate_event'}
          onClick={() => handleAction('duplicate_event', 'Replayed duplicate event (Idempotent deduplication)')}
          icon={<CopyCheck className="w-3.5 h-3.5 text-[var(--color-neutral)]" />}
          className="text-left justify-start h-10 px-3 hover:bg-[var(--color-inset)]"
        >
          <span className="truncate">Duplicate event</span>
        </Button>

        <Button
          size="sm"
          variant="secondary"
          disabled={loading}
          loading={activeAction === 'advance_clock'}
          onClick={() => handleAction('advance_clock', 'Clock offset +30 days (Simulate expiration)')}
          icon={<Clock className="w-3.5 h-3.5 text-[var(--color-bad)]" />}
          className="text-left justify-start h-10 px-3 text-[var(--color-bad)] border-[var(--color-bad-line)] hover:bg-[var(--color-bad-soft)]"
        >
          <span className="truncate">Advance clock +30d</span>
        </Button>
      </div>

      {lastMessage && (
        <div
          role="status"
          aria-live="polite"
          className="text-[12px] font-mono p-3 rounded-lg bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)] flex items-center gap-2.5 animate-in fade-in duration-150"
        >
          <span className="w-2 h-2 rounded-full bg-[var(--color-accent)] animate-pulse shrink-0" />
          <span className="truncate">{lastMessage}</span>
        </div>
      )}
    </div>
  )
}
