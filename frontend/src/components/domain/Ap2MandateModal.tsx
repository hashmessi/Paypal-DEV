import React, { useEffect, useRef, useState } from 'react'
import { Button } from '../ui/Button'
import { X, Copy, Check, Download, ShieldCheck } from 'lucide-react'

export interface Ap2MandateModalProps {
  isOpen: boolean
  onClose: () => void
  mandate: Record<string, unknown> | null
  purchaseRef?: string
}

export const Ap2MandateModal: React.FC<Ap2MandateModalProps> = ({
  isOpen,
  onClose,
  mandate,
  purchaseRef = 'Mandate',
}) => {
  const [copied, setCopied] = useState(false)
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose()
      }
      window.addEventListener('keydown', handleKeyDown)
      return () => {
        window.removeEventListener('keydown', handleKeyDown)
        document.body.style.overflow = ''
      }
    }
  }, [isOpen, onClose])

  if (!isOpen || !mandate) return null

  const jsonString = JSON.stringify(mandate, null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(jsonString)
    const a = document.createElement('a')
    a.setAttribute('href', dataStr)
    a.setAttribute('download', `ap2_mandate_${purchaseRef}.json`)
    document.body.appendChild(a)
    a.click()
    a.remove()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ap2-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div
        ref={dialogRef}
        className="w-full max-w-3xl bg-white rounded-2xl shadow-2xl border border-[var(--color-line)] flex flex-col max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-[var(--color-line)] bg-[var(--color-canvas)]">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#0070ba]/10 text-[#0070ba] border border-[#0070ba]/20">
                <ShieldCheck className="w-3.5 h-3.5" /> Google AP2 v0.2 Protocol
              </span>
              <span className="text-[12px] font-mono text-[var(--color-muted)]">
                RFC 8785 Canonical JSON
              </span>
            </div>
            <h2 id="ap2-modal-title" className="text-[18px] font-semibold text-[var(--color-ink)]">
              Agent Payments Protocol Mandate
            </h2>
            <p className="text-[13px] text-[var(--color-muted)]">
              Carries frozen agent purchasing mandates through checkout to conditional PayPal settlement.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-[var(--color-muted)] hover:text-[var(--color-ink)] hover:bg-[var(--color-inset)] rounded-lg transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Protocol Spec Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-[var(--color-inset)] border-b border-[var(--color-line)] text-[12px]">
          <div className="p-2.5 rounded bg-white border border-[var(--color-line)]">
            <p className="font-semibold text-[var(--color-ink)]">Open Mandate</p>
            <p className="text-[var(--color-muted)] mt-0.5 font-mono text-[11px]">ap2:open_checkout_mandate</p>
            <p className="text-[11px] text-[var(--color-muted)] mt-1">Intent & spending limits</p>
          </div>
          <div className="p-2.5 rounded bg-white border border-[var(--color-line)]">
            <p className="font-semibold text-[var(--color-ink)]">Closed Mandate</p>
            <p className="text-[var(--color-muted)] mt-0.5 font-mono text-[11px]">ap2:closed_checkout_mandate</p>
            <p className="text-[11px] text-[var(--color-muted)] mt-1">RFC 8785 sealed quote hash</p>
          </div>
          <div className="p-2.5 rounded bg-white border border-[var(--color-line)]">
            <p className="font-semibold text-[var(--color-ink)]">Settlement Gate</p>
            <p className="text-[var(--color-muted)] mt-0.5 font-mono text-[11px]">promiseloop:settlement_gate</p>
            <p className="text-[11px] text-[var(--color-muted)] mt-1">Invariants verified pre-capture</p>
          </div>
        </div>

        {/* Code Content */}
        <div className="flex-1 overflow-auto p-4 bg-[#0f172a] text-slate-100 font-mono text-[12px] leading-relaxed">
          <pre className="p-2 select-text">{jsonString}</pre>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between p-4 border-t border-[var(--color-line)] bg-[var(--color-canvas)]">
          <span className="text-[12px] text-[var(--color-muted)] font-mono">
            Bound to PayPal Orders v2 custom_id
          </span>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              icon={copied ? <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" /> : <Copy className="w-3.5 h-3.5" />}
              onClick={handleCopy}
            >
              {copied ? 'Copied' : 'Copy JSON'}
            </Button>
            <Button
              size="sm"
              variant="primary"
              icon={<Download className="w-3.5 h-3.5" />}
              onClick={handleDownload}
            >
              Download .json
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
