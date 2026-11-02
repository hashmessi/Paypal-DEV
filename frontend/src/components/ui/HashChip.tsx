import React, { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { truncateHash, truncateId } from '../../lib/hash'

export interface HashChipProps {
  value: string
  kind?: 'sha' | 'paypal' | 'evt' | 'id'
  copyable?: boolean
  className?: string
}

export const HashChip: React.FC<HashChipProps> = ({
  value,
  kind = 'sha',
  copyable = true,
  className = '',
}) => {
  const [copied, setCopied] = useState(false)

  if (!value) return null

  const displayText = kind === 'sha' ? truncateHash(value) : truncateId(value)

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] text-[12px] font-mono text-[var(--color-ink)] select-all whitespace-nowrap ${className}`}
      title={value}
    >
      <span>{displayText}</span>
      {copyable && (
        <button
          type="button"
          onClick={handleCopy}
          className="p-0.5 text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors rounded focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
          aria-label={`Copy ${kind} ${value}`}
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
    </span>
  )
}

