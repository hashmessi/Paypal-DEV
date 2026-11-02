import React from 'react'

export interface EmptyStateProps {
  title: string
  body: string
  action?: React.ReactNode
  icon?: React.ReactNode
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, body, action, icon }) => {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-4">
      {icon && <div className="p-3 rounded-full bg-[var(--color-inset)] text-[var(--color-muted)] mb-3">{icon}</div>}
      <h3 className="text-[18px] font-semibold text-[var(--color-ink)]">{title}</h3>
      <p className="text-[14px] text-[var(--color-muted)] max-w-md mt-1 mb-4 leading-normal">{body}</p>
      {action && <div>{action}</div>}
    </div>
  )
}

