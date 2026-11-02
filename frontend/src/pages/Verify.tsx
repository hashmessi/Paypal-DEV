import React, { useState, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Banner } from '../components/ui/Banner'
import { HashChip } from '../components/ui/HashChip'
import { verifyReceiptJson } from '../lib/hash'
import { ShieldCheck, Sparkles, AlertTriangle } from 'lucide-react'

type Result = { match: boolean; claimed: string; computed: string } | { error: string }

const SAMPLE_RECEIPT = JSON.stringify(
  {
    version: 1,
    currency: 'USD',
    total_cents: 39900,
    constraints: {
      product_type: 'Over-ear headphones',
      condition: 'new',
      variant_color: 'black',
      max_total_cents: 40000,
      deliver_within_days: 5,
    },
    product_snapshot: {
      title: 'Sony WH-1000XM5 Noise Canceling Headphones - Black',
      sku: 'WH1000XM5-BLK-NEW',
    },
    merchant_quote: {
      seller_domain: 'bestbuy.example.com',
      total_cents: 39900,
      sku: 'WH1000XM5-BLK-NEW',
      currency: 'USD',
    },
    capture_conditions: {
      require_carrier_acceptance: true,
      reject_label_created_alone: true,
      reject_refurbished: true,
      max_delivery_days: 5,
      expected_sku: 'WH1000XM5-BLK-NEW',
      expected_color: null,
    },
    receipt_hash: '81cc87fd716d897896abb4dbe0f69f626ddf0dfec6dd9eb56feb46a793b69577',
  },
  null,
  2
)

export const VerifyPage: React.FC = () => {
  const location = useLocation()
  const initialText = (location.state as { receiptJson?: string } | null)?.receiptJson || ''
  const [text, setText] = useState(initialText)
  const [result, setResult] = useState<Result | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)

  const runVerification = useCallback(async (content: string) => {
    if (!content.trim()) return
    setIsVerifying(true)
    try {
      setResult(await verifyReceiptJson(content))
    } catch (e) {
      setResult({ error: e instanceof Error ? e.message : String(e) })
    } finally {
      setIsVerifying(false)
    }
  }, [])

  useEffect(() => {
    if (initialText) {
      const timer = setTimeout(() => {
        void runVerification(initialText)
      }, 0)
      return () => clearTimeout(timer)
    }
  }, [initialText, runVerification])

  const handleLoadSample = () => {
    setText(SAMPLE_RECEIPT)
    void runVerification(SAMPLE_RECEIPT)
  }

  const handleTamperSample = () => {
    try {
      const parsed = JSON.parse(text || SAMPLE_RECEIPT)
      parsed.total_cents = (parsed.total_cents || 39900) + 100 // alter price by $1
      const tampered = JSON.stringify(parsed, null, 2)
      setText(tampered)
      void runVerification(tampered)
    } catch {
      setText(SAMPLE_RECEIPT.replace('39900', '39901'))
      void runVerification(SAMPLE_RECEIPT.replace('39900', '39901'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="OFFLINE CRYPTOGRAPHIC VERIFIER"
        title="Verify a receipt"
        description="Paste a Promise Receipt JSON (body of GET /receipts/{id}). The RFC 8785 canonical JSON and SHA-256 hash are independently recomputed inside your browser via WebCrypto."
      />

      <Card>
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <span className="text-[12px] font-semibold text-[var(--color-muted)] uppercase tracking-wider">
              Receipt JSON payload
            </span>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="secondary" onClick={handleLoadSample} icon={<Sparkles className="w-3.5 h-3.5" />}>
                Load sample
              </Button>
              <Button size="sm" variant="ghost" onClick={handleTamperSample} icon={<AlertTriangle className="w-3.5 h-3.5 text-[var(--color-warn)]" />}>
                Simulate tamper (+1¢)
              </Button>
            </div>
          </div>

          <textarea
            aria-label="Receipt JSON"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            spellCheck={false}
            placeholder="Paste raw Promise Receipt JSON here, or click 'Load sample' above..."
            className="w-full font-mono text-[12px] p-3 rounded-[var(--radius-control)] border border-[var(--color-line)] bg-[var(--color-inset)] text-[var(--color-ink)] focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
          />

          <div className="flex items-center justify-between flex-wrap gap-3 pt-1">
            <div className="flex items-center gap-3">
              <Button
                variant="primary"
                onClick={() => runVerification(text)}
                disabled={!text.trim()}
                loading={isVerifying}
                icon={<ShieldCheck className="w-4 h-4" />}
              >
                Recompute SHA-256
              </Button>
              <span className="text-[12px] text-[var(--color-muted)]">
                Computed locally via WebCrypto; zero server calls.
              </span>
            </div>
            {text && (
              <Button size="sm" variant="ghost" onClick={() => { setText(''); setResult(null); }}>
                Clear
              </Button>
            )}
          </div>
        </div>
      </Card>

      {result && 'error' in result && (
        <Banner tone="bad" title="Cannot verify payload" body={result.error} />
      )}

      {result && 'match' in result && (
        <div className="space-y-3">
          <Banner
            tone={result.match ? 'ok' : 'bad'}
            title={result.match ? 'MATCH: Cryptographic Integrity Intact' : 'MISMATCH: Alteration Detected'}
            body={
              result.match
                ? 'The RFC 8785 canonical JSON digest strictly matches the claimed receipt_hash. Every constraint, price, and condition is tamper-sealed.'
                : 'The computed hash does not match the claimed receipt_hash. The payload was modified after buyer approval or is not an authentic sealed receipt.'
            }
          />
          <div className="p-4 rounded-[var(--radius-card)] bg-white border border-[var(--color-line)] space-y-2 text-[14px]">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[var(--color-muted)] w-24 shrink-0 font-medium">Claimed hash</span>
              <HashChip value={result.claimed} full />
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[var(--color-muted)] w-24 shrink-0 font-medium">Computed hash</span>
              <HashChip value={result.computed} full />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
