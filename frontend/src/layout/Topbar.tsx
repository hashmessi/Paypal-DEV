import React from 'react'
import { useLocation } from 'react-router'
import { Badge } from '../components/ui/Badge'
import { Clock, Menu, ShieldCheck } from 'lucide-react'
import { getDemoClockOffsetMs, setDemoClockOffsetDays } from '../lib/time'

export interface TopbarProps {
  onToggleMobile?: () => void
}

export const Topbar: React.FC<TopbarProps> = ({ onToggleMobile }) => {
  const location = useLocation()
  const offsetMs = getDemoClockOffsetMs()
  const isClockSimulated = offsetMs > 0

  const getPageTitle = (pathname: string): string => {
    if (pathname === '/') return 'Judge start'
    if (pathname.startsWith('/shop')) return 'Shopper agent'
    if (pathname.startsWith('/receipts/') && pathname.endsWith('/replay')) return 'Promise replay'
    if (pathname.startsWith('/receipts/')) return 'Promise receipt'
    if (pathname === '/receipts') return 'Promise receipts'
    if (pathname.startsWith('/tower/cases/')) return 'Drift review'
    if (pathname.startsWith('/tower')) return 'Control tower'
    if (pathname === '/proof') return 'Proof'
    if (pathname === '/verify') return 'Verify receipt'
    if (pathname === '/events') return 'Event history'
    if (pathname === '/spine') return 'Spine console'
    return 'Control tower'
  }

  const currentTitle = getPageTitle(location.pathname)

  const handleResetClock = (e: React.MouseEvent) => {
    e.stopPropagation()
    setDemoClockOffsetDays(0)
    window.location.reload()
  }

  return (
    <header className="h-16 border-b border-[var(--color-line)] bg-[var(--color-surface)] px-4 md:px-8 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      <div className="flex items-center gap-3">
        {onToggleMobile && (
          <button
            type="button"
            onClick={onToggleMobile}
            className="md:hidden p-1.5 rounded-lg text-[var(--color-ink)] hover:bg-[var(--color-inset)] focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] cursor-pointer"
            aria-label="Toggle navigation drawer"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="flex items-center gap-2 text-[14px]">
          <span className="text-[var(--color-muted)] hidden sm:inline font-medium">Demo Merchant A</span>
          <span className="text-[var(--color-line-strong)] hidden sm:inline">/</span>
          <span className="text-[var(--color-ink)] font-semibold tracking-tight">{currentTitle}</span>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {isClockSimulated && (
          <button
            type="button"
            onClick={handleResetClock}
            title="Click to reset simulated clock to real time"
            className="cursor-pointer"
          >
            <Badge tone="warn" icon={<Clock className="w-3.5 h-3.5" />}>
              <span>+30d Simulated</span>
              <span className="underline ml-1 font-normal opacity-80 hover:opacity-100">Reset</span>
            </Badge>
          </button>
        )}

        <Badge tone="ok" dot={true} className="hidden sm:inline-flex">
          PayPal Sandbox
        </Badge>

        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--color-inset)] border border-[var(--color-line)] text-[12px] font-mono text-[var(--color-muted)]">
          <ShieldCheck className="w-3.5 h-3.5 text-[var(--color-accent)]" />
          <span>CAS v2 Sealed</span>
        </div>
      </div>
    </header>
  )
}
