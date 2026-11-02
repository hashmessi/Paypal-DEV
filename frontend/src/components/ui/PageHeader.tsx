import React from 'react'

export interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  actions?: React.ReactNode
  status?: React.ReactNode
}

export const PageHeader: React.FC<PageHeaderProps> = ({ eyebrow, title, description, actions, status }) => {
  return (
    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 pb-6 border-b border-[var(--color-line)] mb-6">
      <div className="space-y-1">
        {eyebrow && (
          <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">{eyebrow}</p>
        )}
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-[28px] font-semibold text-[var(--color-ink)] leading-tight">{title}</h1>
          {status}
        </div>
        {description && <p className="text-[14px] text-[var(--color-muted)] max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-3 shrink-0 flex-wrap self-start">{actions}</div>}
    </div>
  )
}

