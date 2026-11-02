import React, { useState } from 'react'
import { PageHeader } from '../components/ui/PageHeader'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Banner } from '../components/ui/Banner'
import { HashChip } from '../components/ui/HashChip'
import { verifyReceiptJson } from '../lib/hash'

type Result = { match: boolean; claimed: string; computed: string } | { error: string }

export const VerifyPage: React.FC = () => {
  const [text, setText] = useState('')
  const [result, setResult] = useState<Result | null>(null)

  const run = async () => {
    try {
      setResult(await verifyReceiptJson(text))
    } catch (e) {
      setResult({ error: e instanceof Error ? e.message : String(e) })
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="OFFLINE VERIFIER"
        title="Verify a receipt"
        description="Paste a Promise Receipt JSON (the body of GET /receipts/{id}). The SHA-256 is recomputed here, in your browser."
      />
      <Card>
        <div className="space-y-4">
          <textarea
            aria-label="Receipt JSON"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
            spellCheck={false}
            className="w-full font-mono text-[12px] p-3 rounded-[var(--radius-control)] border border-[var(--color-line)] bg-[var(--color-inset)] text-[var(--color-ink)]"
          />
          <div className="flex items-center gap-3">
            <Button variant="primary" onClick={run} disabled={!text.trim()}>Verify</Button>
            <span className="text-[12px] text-[var(--color-muted)]">Computed locally in your browser, no server call.</span>
          </div>
        </div>
      </Card>
      {result && 'error' in result && <Banner tone="bad" title="Cannot verify" body={result.error} />}
      {result && 'match' in result && (
        <div className="space-y-3">
          <Banner
            tone={result.match ? 'ok' : 'bad'}
            title={result.match ? 'MATCH' : 'MISMATCH'}
            body={result.match ? 'The receipt contents hash to the claimed receipt_hash.' : 'The receipt contents do not hash to the claimed receipt_hash. It was altered or is not a sealed receipt.'}
          />
          <div className="text-[14px] space-y-1">
            <div className="flex items-center gap-2"><span className="text-[var(--color-muted)] w-20">Claimed</span><HashChip value={result.claimed} full /></div>
            <div className="flex items-center gap-2"><span className="text-[var(--color-muted)] w-20">Computed</span><HashChip value={result.computed} full /></div>
          </div>
        </div>
      )}
    </div>
  )
}
