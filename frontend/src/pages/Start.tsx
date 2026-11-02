import React, { useState } from 'react'
import { useNavigate } from 'react-router'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useTower } from '../queries/useTower'
import { ArrowRight, Copy, Check, Play } from 'lucide-react'

export const StartPage: React.FC = () => {
  const navigate = useNavigate()
  const { runDemoScenario, isRunningDemo } = useTower()
  const [copiedEmail, setCopiedEmail] = useState(false)
  const [copiedPass, setCopiedPass] = useState(false)

  const handleRunDemo = async () => {
    try {
      const res = await runDemoScenario()
      navigate(`/receipts/${res.purchase_id}`)
    } catch (err) {
      console.error('Failed to run demo scenario', err)
    }
  }

  const copyCred = (text: string, type: 'email' | 'pass') => {
    navigator.clipboard.writeText(text)
    if (type === 'email') {
      setCopiedEmail(true)
      setTimeout(() => setCopiedEmail(false), 1500)
    } else {
      setCopiedPass(true)
      setTimeout(() => setCopiedPass(false), 1500)
    }
  }

  return (
    <div className="max-w-[720px] mx-auto py-6 sm:py-10 space-y-8">
      {/* Eyebrow & Hero Header */}
      <div className="space-y-2">
        <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-accent)]">
          PROMISE-GATED PAYMENTS FOR AGENTIC COMMERCE
        </p>
        <h1 className="text-[28px] font-semibold text-[var(--color-ink)] leading-tight">
          Capture only what the buyer approved
        </h1>
        <p className="text-[14px] text-[var(--color-muted)] leading-relaxed">
          When autonomous shopping agents buy for humans, merchants should only settle funds if physical fulfillment
          provably matches the frozen buyer agreement. Any product, price, or carrier drift locks the hold.
        </p>
      </div>

      {/* Primary Action Button */}
      <div className="p-6 rounded-[var(--radius-card)] bg-white border border-[var(--color-line)] shadow-[var(--shadow-card)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-[18px] font-semibold text-[var(--color-ink)]">
              Interactive 8-Act Walkthrough
            </h2>
            <p className="text-[14px] text-[var(--color-muted)] mt-0.5">
              Instantiates a fresh clock-relative purchase, approval, and authorization.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4 fill-current" />}
            loading={isRunningDemo}
            onClick={handleRunDemo}
            className="shrink-0"
          >
            Run demo scenario
          </Button>
        </div>

        <div className="flex items-center gap-4 pt-3 border-t border-[var(--color-line)] text-[13px]">
          <button
            type="button"
            onClick={() => navigate('/shop')}
            className="text-[var(--color-accent)] hover:underline font-semibold flex items-center gap-1"
          >
            Step-by-step shopper flow <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <span className="text-[var(--color-line-strong)]">·</span>
          <button
            type="button"
            onClick={() => navigate('/proof')}
            className="text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors"
          >
            View verification proof & metrics
          </button>
        </div>
      </div>

      {/* Guide: How to test */}
      <Card title="How to test (5 minutes)" subtitle="Complete the full loop unaided in three straightforward steps">
        <ol className="space-y-4 my-2 text-[14px]">
          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)] font-semibold text-[12px] flex items-center justify-center shrink-0 mt-0.5">
              1
            </span>
            <div className="space-y-1">
              <p className="font-semibold text-[var(--color-ink)]">Launch the scenario</p>
              <p className="text-[var(--color-muted)] leading-relaxed">
                Click <strong>Run demo scenario</strong> above or create your own search query via the Shopper Agent.
                The agreement compiles into a cryptographic SHA-256 Promise Receipt.
              </p>
            </div>
          </li>

          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)] font-semibold text-[12px] flex items-center justify-center shrink-0 mt-0.5">
              2
            </span>
            <div className="space-y-1">
              <p className="font-semibold text-[var(--color-ink)]">Authorize the payment hold</p>
              <p className="text-[var(--color-muted)] leading-relaxed">
                Approve the frozen receipt hash. Funds are held in PayPal Orders v2 Sandbox with status{' '}
                <span className="font-semibold text-[var(--color-warn)]">Authorized · not captured</span>.
              </p>
            </div>
          </li>

          <li className="flex items-start gap-3">
            <span className="w-6 h-6 rounded-full bg-[var(--color-inset)] text-[var(--color-ink)] border border-[var(--color-line)] font-semibold text-[12px] flex items-center justify-center shrink-0 mt-0.5">
              3
            </span>
            <div className="space-y-1">
              <p className="font-semibold text-[var(--color-ink)]">Simulate drift and recovery</p>
              <p className="text-[var(--color-muted)] leading-relaxed">
                Use the <strong>Scenario Console</strong> on the receipt to trigger a refurbished item mismatch.
                Observe the instant <span className="font-semibold text-[var(--color-bad)]">CAPTURE BLOCKED</span> gate,
                inspect the expected vs observed drift in the Control Tower, and click{' '}
                <strong>Send correct item + carrier</strong> to verify automatic capture.
              </p>
            </div>
          </li>
        </ol>

        {/* Sandbox test account */}
        <div className="mt-5 p-4 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2">
          <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
            PayPal Sandbox Buyer Credentials
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[13px] font-mono">
            <div className="flex items-center justify-between p-2 rounded bg-white border border-[var(--color-line)]">
              <span className="truncate mr-2">sb-buyer-promiseloop@personal.example.com</span>
              <button
                type="button"
                onClick={() => copyCred('sb-buyer-promiseloop@personal.example.com', 'email')}
                className="p-1 hover:text-[var(--color-accent)] focus-visible:outline-2"
                aria-label="Copy buyer sandbox email"
              >
                {copiedEmail ? <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            <div className="flex items-center justify-between p-2 rounded bg-white border border-[var(--color-line)]">
              <span>Password1!</span>
              <button
                type="button"
                onClick={() => copyCred('Password1!', 'pass')}
                className="p-1 hover:text-[var(--color-accent)] focus-visible:outline-2"
                aria-label="Copy buyer sandbox password"
              >
                {copiedPass ? <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Honest Boundary Disclosure */}
      <Card title="What is simulated vs real" subtitle="Transparent system boundaries per UI-SPEC">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[13px]">
          <div className="space-y-1.5 p-3 rounded bg-[var(--color-canvas)] border border-[var(--color-line)]">
            <p className="font-semibold text-[var(--color-ink)] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--color-ok)]" /> Real Systems
            </p>
            <p className="text-[var(--color-muted)] leading-relaxed">
              PayPal Orders v2 authorization holds, capture executions, status polling, and SHA-256 cryptographic receipt verification.
            </p>
          </div>

          <div className="space-y-1.5 p-3 rounded bg-[var(--color-canvas)] border border-[var(--color-line)]">
            <p className="font-semibold text-[var(--color-ink)] flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--color-warn)]" /> Simulated (SYNTHETIC)
            </p>
            <p className="text-[var(--color-muted)] leading-relaxed">
              Warehouse order-line pick events and carrier tracking scans (UPS/FedEx) are generated by the Scenario Console test harness.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

