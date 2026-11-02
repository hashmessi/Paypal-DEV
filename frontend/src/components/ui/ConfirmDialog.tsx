import React, { useEffect, useRef, useState } from 'react'
import { Button } from './Button'
import { AlertTriangle, X } from 'lucide-react'

export interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  body: React.ReactNode
  confirmLabel: string
  cancelLabel?: string
  destructive?: boolean
  requireReason?: boolean
  reasonOptions?: { value: string; label: string }[]
  onConfirm: (reason?: string) => void
  onClose: () => void
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  body,
  confirmLabel,
  cancelLabel = 'Keep authorization',
  destructive = true,
  requireReason = false,
  reasonOptions = [
    { value: '', label: 'Select a reason code...' },
    { value: 'buyer_cancelled', label: 'Cancelled by buyer' },
    { value: 'out_of_stock', label: 'Out of stock' },
    { value: 'contract_violation', label: 'Contract violation' },
    { value: 'other', label: 'Other merchant reason' },
  ],
  onConfirm,
  onClose,
}) => {
  const [reason, setReason] = useState('')
  const dialogRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement
      document.body.style.overflow = 'hidden'

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose()
        }
      }
      window.addEventListener('keydown', handleKeyDown)
      return () => {
        window.removeEventListener('keydown', handleKeyDown)
        document.body.style.overflow = ''
        previousActiveElement.current?.focus()
      }
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const isConfirmDisabled = requireReason && !reason

  const handleClose = () => {
    setReason('')
    onClose()
  }

  const handleConfirm = () => {
    onConfirm(reason)
    setReason('')
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div
        ref={dialogRef}
        className="w-full max-w-lg bg-white rounded-2xl border border-[var(--color-line)] shadow-[var(--shadow-modal)] p-6 space-y-5 animate-in zoom-in-95 duration-150 relative"
      >
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-5 right-5 p-1 rounded-md text-[var(--color-muted)] hover:text-[var(--color-ink)] hover:bg-[var(--color-inset)] transition-colors focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] cursor-pointer"
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-start gap-3.5 pr-6">
          {destructive && (
            <div className="p-2.5 rounded-xl bg-[var(--color-bad-soft)] text-[var(--color-bad)] border border-[var(--color-bad-line)] shrink-0">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
            </div>
          )}
          <div className="space-y-1">
            <h2 id="dialog-title" className="text-[18px] font-semibold text-[var(--color-ink)] leading-snug">
              {title}
            </h2>
            <div className="text-[14px] text-[var(--color-muted)] leading-relaxed">{body}</div>
          </div>
        </div>

        {requireReason && (
          <div className="space-y-1.5 pt-1">
            <label htmlFor="void-reason-select" className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-ink)] block">
              Reason code (required)
            </label>
            <select
              id="void-reason-select"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full h-10 px-3 bg-white border border-[var(--color-line)] hover:border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px] text-[var(--color-ink)] focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2 transition-colors cursor-pointer"
              required
            >
              {reasonOptions.map((opt) => (
                <option key={opt.value} value={opt.value} disabled={opt.value === ''}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--color-line)]">
          <Button variant="secondary" onClick={handleClose}>
            {cancelLabel}
          </Button>
          <Button
            variant={destructive ? 'danger-solid' : 'primary'}
            disabled={isConfirmDisabled}
            onClick={handleConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
