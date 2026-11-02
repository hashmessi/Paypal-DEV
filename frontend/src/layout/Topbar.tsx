import React from 'react'
import { useLocation } from 'react-router'
import { Badge } from '../components/ui/Badge'
import { Clock, Menu } from 'lucide-react'
import { getDemoClockOffsetMs } from '../lib/time'

export interface TopbarProps {
  onToggleMobile?: () => void
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleMobile }) => {
  const location = useLocation()
  const offsetMs = getDemoClockOffsetMs()
  const isClockSimulated = offsetMs > 0

  const getPageTitle = (pathname: string): string => {
    if (pathname === '/') return 'Judge Start'
    if (pathname.startsWith('/shop')) return 'Shopper agent'
    if (pathname.startsWith('/receipts/') && pathname.endsWith('/replay')) return 'Promise Replay'
    if (pathname.startsWith('/receipts/')) return 'Promise Receipt'
    if (pathname === '/receipts') return 'Promise receipts'
    if (pathname.startsWith('/tower/cases/')) return 'Drift review'
    if (pathname.startsWith('/tower')) return 'Control tower'
    if (pathname === '/proof') return 'Proof'
    if (pathname === '/events') return 'Event history'
    if (pathname === '/spine') return 'Spine Console'
    return 'Control tower'
  }

  const currentTitle = getPageTitle(location.pathname)

  return (
    <header className="h-16 border-b border-[var(--color-line)] bg-[var(--color-surface)] px-4 md:px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        {onToggleMobile && (
          <button
            type="button"
            onClick={onToggleMobile}
            className="md:hidden p-1.5 rounded text-[var(--color-ink)] hover:bg-[var(--color-canvas)] focus-visible:outline-2"
            aria-label="Toggle navigation drawer"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="flex items-center gap-2 text-[14px]">
          <span className="text-[var(--color-muted)] hidden sm:inline">Demo Merchant A</span>
          <span className="text-[var(--color-line-strong)] hidden sm:inline">/</span>
          <span className="text-[var(--color-ink)] font-semibold">{currentTitle}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {isClockSimulated && (
          <Badge tone="warn" icon={<Clock className="w-3.5 h-3.5" />}>
            Simulated time +30d
          </Badge>
        )}

        <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-[0.04em] bg-[var(--color-neutral-soft)] text-[var(--color-neutral)] border border-[var(--color-neutral-line)]">
          SANDBOX ENVIRONMENT
        </span>

        <div
          className="w-8 h-8 rounded-full bg-[var(--color-ink)] text-white text-[12px] font-semibold flex items-center justify-center shrink-0"
          title="Demo Merchant A (Sandbox)"
        >
          DM
        </div>
      </div>
    </header>
  )
}
