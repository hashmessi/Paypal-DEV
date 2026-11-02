import React from 'react'
import { NavLink, useLocation } from 'react-router'
import {
  LayoutGrid,
  FileText,
  AlertOctagon,
  Activity,
  ShoppingBag,
  ShieldCheck,
  Compass,
  Terminal,
  CheckCircle2,
  X,
} from 'lucide-react'

export interface SidebarProps {
  driftCount?: number
  isMobileOpen?: boolean
  onCloseMobile?: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ driftCount = 0, isMobileOpen, onCloseMobile }) => {
  const { pathname, search } = useLocation()
  const onDriftView = pathname === '/tower' && new URLSearchParams(search).get('filter') === 'drift'

  const workspaceLinks = [
    { to: '/tower', label: 'Control tower', icon: LayoutGrid },
    { to: '/receipts', label: 'Promise receipts', icon: FileText },
    {
      to: '/tower?filter=drift',
      label: 'Drift queue',
      icon: AlertOctagon,
      badge: driftCount > 0 ? driftCount : undefined,
    },
    { to: '/events', label: 'Event history', icon: Activity },
  ]

  const demoLinks = [
    { to: '/', label: 'Judge start', icon: Compass },
    { to: '/shop', label: 'Shopper agent', icon: ShoppingBag },
    { to: '/proof', label: 'Proof', icon: ShieldCheck },
    { to: '/spine', label: 'Spine console', icon: Terminal },
  ]

  const renderNavGroup = (title: string, links: typeof workspaceLinks) => (
    <div className="space-y-1 py-2">
      <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--color-muted)] hidden md:block">
        {title}
      </p>
      {links.map((link) => {
        const Icon = link.icon
        return (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/' || link.to === '/tower'}
            onClick={onCloseMobile}
            className={({ isActive }) => {
              // NavLink ignores the query string, so the two /tower links are resolved by hand.
              const active =
                link.to === '/tower'
                  ? pathname === '/tower' && !onDriftView
                  : link.to === '/tower?filter=drift'
                    ? onDriftView || pathname.startsWith('/tower/cases')
                    : isActive
              return `flex items-center justify-between h-10 px-3 rounded-[var(--radius-control)] text-[14px] transition-all duration-150 ${
                active
                  ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-semibold shadow-2xs'
                  : 'text-[var(--color-ink)] hover:bg-[var(--color-inset)] hover:text-[var(--color-accent)] font-normal'
              }`
            }}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-105" aria-hidden="true" />
              <span className="truncate hidden md:inline">{link.label}</span>
            </div>
            {link.badge !== undefined && (
              <span
                className="px-1.5 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)] shrink-0 hidden md:inline-flex"
                aria-label={`${link.badge} open drift cases`}
              >
                {link.badge}
              </span>
            )}
          </NavLink>
        )
      })}
    </div>
  )

  const mobileDrawerClass = isMobileOpen
    ? 'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-2xl block animate-in slide-in-from-left duration-200'
    : 'hidden md:flex'

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs md:hidden animate-in fade-in duration-150"
          aria-hidden="true"
        />
      )}

      <aside
        className={`w-16 md:w-[232px] shrink-0 border-r border-[var(--color-line)] bg-[var(--color-surface)] flex-col justify-between h-screen sticky top-0 z-40 ${mobileDrawerClass}`}
      >
        <div>
          {/* Brand header */}
          <div className="h-16 flex items-center justify-between px-4 md:px-5 border-b border-[var(--color-line)]">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-[8px] bg-gradient-to-br from-[#003087] to-[#0070ba] text-white flex items-center justify-center font-black text-[15px] shadow-xs shrink-0 select-none">
                P
              </div>
              <div className="min-w-0 hidden md:block">
                <span className="text-[17px] font-bold text-[var(--color-ink)] tracking-tight block leading-tight">
                  PromiseLoop
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.05em] text-[var(--color-accent)] block -mt-0.5">
                  PayPal Agent Commerce
                </span>
              </div>
            </div>

            {isMobileOpen && (
              <button
                type="button"
                onClick={onCloseMobile}
                className="md:hidden p-1 rounded-md text-[var(--color-muted)] hover:text-[var(--color-ink)] hover:bg-[var(--color-inset)]"
                aria-label="Close sidebar"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Nav groups */}
          <nav className="p-2 md:p-3 space-y-1">
            {renderNavGroup('Workspace', workspaceLinks)}
            <div className="h-[1px] bg-[var(--color-line)] my-1" />
            {renderNavGroup('Demo & Testing', demoLinks)}
          </nav>
        </div>

        {/* Footer merchant card */}
        <div className="p-3 border-t border-[var(--color-line)] hidden md:block">
          <div className="p-2.5 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] hover:border-[var(--color-line-strong)] transition-colors flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 text-white text-[12px] font-bold flex items-center justify-center shrink-0 shadow-2xs">
              DM
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1">
                <p className="text-[12px] font-semibold text-[var(--color-ink)] truncate leading-tight">
                  Demo Merchant A
                </p>
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-ok)] shrink-0" aria-label="Verified PayPal Merchant" />
              </div>
              <p className="text-[11px] text-[var(--color-muted)] truncate mt-0.5">PayPal Sandbox · Live CAS</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
