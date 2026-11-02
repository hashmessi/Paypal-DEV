import React, { useState } from 'react'
import { Copy, Check } from 'lucide-react'

export interface KeyValueRowProps {
  label: string
  value: React.ReactNode
  mono?: boolean
  copyValue?: string
  divider?: boolean
}

export const KeyValueRow: React.FC<KeyValueRowProps> = ({
  label,
  value,
  mono = false,
  copyValue,
  divider = true,
}) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    if (!copyValue && typeof value !== 'string') return
    const textToCopy = copyValue || (typeof value === 'string' ? value : '')
    navigator.clipboard.writeText(textToCopy)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div
      className={`flex items-center justify-between py-2.5 text-[14px] ${
        divider ? 'border-b border-[var(--color-line)]' : ''
      }`}
    >
      <span className="text-[var(--color-muted)] font-normal">{label}</span>
      <div className="flex items-center gap-1.5 font-semibold text-[var(--color-ink)] text-right">
        <span className={mono ? 'font-mono text-[13px]' : ''}>{value}</span>
        {(copyValue || typeof value === 'string') && copyValue !== undefined && (
          <button
            type="button"
            onClick={handleCopy}
            className="p-1 text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] rounded"
            aria-label={`Copy ${label}`}
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" aria-hidden="true" />
            ) : (
              <Copy className="w-3.5 h-3.5" aria-hidden="true" />
            )}
            <span className="sr-only" role="status" aria-live="polite">
              {copied ? 'Copied' : ''}
            </span>
          </button>
        )}
      </div>
    </div>
  )
}

export interface KeyValueGridProps {
  children: React.ReactNode
  columns?: 1 | 2 | 3
}

export const KeyValueGrid: React.FC<KeyValueGridProps> = ({ children, columns = 2 }) => {
  const colClass = columns === 3 ? 'md:grid-cols-3' : columns === 2 ? 'md:grid-cols-2' : 'grid-cols-1'

  return <div className={`grid grid-cols-1 ${colClass} gap-x-8 gap-y-1`}>{children}</div>
}

