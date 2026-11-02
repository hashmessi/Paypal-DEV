import React from 'react'
import { NavLink } from 'react-router'
import {
  LayoutGrid,
  FileText,
  AlertOctagon,
  Activity,
  ShoppingBag,
  ShieldCheck,
  Compass,
  Terminal,
} from 'lucide-react'

export interface SidebarProps {
  driftCount?: number
  isMobileOpen?: boolean
  onCloseMobile?: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({ driftCount = 0, isMobileOpen, onCloseMobile }) => {
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
    { to: '/', label: 'Judge Start', icon: Compass },
    { to: '/shop', label: 'Shopper agent', icon: ShoppingBag },
    { to: '/proof', label: 'Proof', icon: ShieldCheck },
    { to: '/spine', label: 'Spine Console', icon: Terminal },
  ]

  const renderNavGroup = (title: string, links: typeof workspaceLinks) => (
    <div className="space-y-1 py-2">
      <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)] hidden md:block">
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
            className={({ isActive }) =>
              `flex items-center justify-between h-10 px-3 rounded-[var(--radius-control)] text-[14px] transition-colors ${
                isActive
                  ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-semibold'
                  : 'text-[var(--color-ink)] hover:bg-[var(--color-canvas)] font-normal'
              }`
            }
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span className="truncate hidden md:inline">{link.label}</span>
            </div>
            {link.badge !== undefined && (
              <span
                className="px-1.5 py-0.2 rounded-full text-[11px] font-semibold bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)] shrink-0 hidden md:inline-flex"
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
    ? 'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl block'
    : 'hidden md:flex'

  return (
    <aside
      className={`w-16 md:w-[232px] shrink-0 border-r border-[var(--color-line)] bg-[var(--color-surface)] flex-col justify-between h-screen sticky top-0 ${mobileDrawerClass}`}
    >
      <div>
        {/* Brand header */}
        <div className="h-16 flex items-center px-4 md:px-5 gap-2.5 border-b border-[var(--color-line)]">
          <div className="w-6 h-6 rounded-[6px] bg-[var(--color-accent)] text-white flex items-center justify-center font-bold text-[14px] shrink-0">
            P
          </div>
          <span className="text-[18px] font-semibold text-[var(--color-ink)] tracking-tight hidden md:inline">
            PromiseLoop
          </span>
        </div>

        {/* Nav groups */}
        <nav className="p-2 md:p-3 space-y-2">
          {renderNavGroup('Workspace', workspaceLinks)}
          <div className="h-[1px] bg-[var(--color-line)] my-1" />
          {renderNavGroup('Demo', demoLinks)}
        </nav>
      </div>

      {/* Footer merchant card */}
      <div className="p-3 border-t border-[var(--color-line)] hidden md:block">
        <div className="p-2.5 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-[var(--color-ink)] text-white text-[12px] font-semibold flex items-center justify-center shrink-0">
            DM
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-semibold text-[var(--color-ink)] truncate leading-tight">
              Demo Merchant A
            </p>
            <p className="text-[11px] text-[var(--color-muted)] truncate">Merchant workspace</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

