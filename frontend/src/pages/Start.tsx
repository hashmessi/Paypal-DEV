import React, { useState } from 'react'
import { useNavigate } from 'react-router'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useTower } from '../queries/useTower'
import { Copy, Check, Play, ShieldCheck, CheckCircle2 } from 'lucide-react'

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
    <div className="max-w-4xl mx-auto py-6 sm:py-10 space-y-8">
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

      {/* Two-Lane Golden Path Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Lane 1: Real PayPal Sandbox Lane */}
        <div className="p-6 rounded-[var(--radius-card)] bg-white border-2 border-[#0070ba]/30 hover:border-[#0070ba] shadow-[var(--shadow-card)] transition-all flex flex-col justify-between space-y-5">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#0070ba]/10 text-[#0070ba] border border-[#0070ba]/20">
                <ShieldCheck className="w-3.5 h-3.5" /> Real PayPal Sandbox
              </span>
              <span className="text-[11px] font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                Lane 1
              </span>
            </div>

            <div>
              <h2 className="text-[18px] font-semibold text-[var(--color-ink)] leading-snug">
                Real PayPal Sandbox Flow
              </h2>
              <p className="text-[14px] text-[var(--color-muted)] leading-relaxed mt-1">
                Real Orders v2 authorization popup with live sandbox credentials, custom_id receipt hash binding, and live capture & Orders v2 tracking push.
              </p>
            </div>

            {/* Sandbox Credentials Box */}
            <div className="p-3.5 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-[var(--color-muted)]">
                Sandbox Buyer Credentials
              </p>
              <div className="space-y-1.5 text-[12px] font-mono">
                <div className="flex items-center justify-between p-2 rounded bg-white border border-[var(--color-line)]">
                  <span className="truncate mr-2 text-[var(--color-ink)]">sb-buyer-promiseloop@personal.example.com</span>
                  <button
                    type="button"
                    onClick={() => copyCred('sb-buyer-promiseloop@personal.example.com', 'email')}
                    className="p-1 hover:text-[var(--color-accent)] focus-visible:outline-2 cursor-pointer"
                    aria-label="Copy buyer sandbox email"
                  >
                    {copiedEmail ? <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-white border border-[var(--color-line)]">
                  <span className="text-[var(--color-ink)]">Password1!</span>
                  <button
                    type="button"
                    onClick={() => copyCred('Password1!', 'pass')}
                    className="p-1 hover:text-[var(--color-accent)] focus-visible:outline-2 cursor-pointer"
                    aria-label="Copy buyer sandbox password"
                  >
                    {copiedPass ? <Check className="w-3.5 h-3.5 text-[var(--color-ok)]" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2">
            <Button
              variant="primary"
              size="md"
              onClick={() => navigate('/shop')}
              className="w-full justify-center text-[14px]"
            >
              Launch Real Sandbox Flow →
            </Button>
          </div>
        </div>

        {/* Lane 2: Instant 30-Sec Demo Lane */}
        <div className="p-6 rounded-[var(--radius-card)] bg-white border border-[var(--color-line)] hover:border-[var(--color-line-strong)] shadow-[var(--shadow-card)] transition-all flex flex-col justify-between space-y-5">
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                <Play className="w-3 h-3 fill-current" /> Instant 30-sec Demo
              </span>
              <span className="text-[11px] font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                Lane 2
              </span>
            </div>

            <div>
              <h2 className="text-[18px] font-semibold text-[var(--color-ink)] leading-snug">
                Instant 30-Sec Evaluation
              </h2>
              <p className="text-[14px] text-[var(--color-muted)] leading-relaxed mt-1">
                1-click deterministic execution. Zero setup required. Generates synthetic quote, simulated authorization hold, and triggers the Promise drift gate.
              </p>
            </div>

            <div className="p-3.5 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2 text-[12px]">
              <p className="font-semibold text-[var(--color-ink)] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-ok)]" /> Deterministic 1-Click Execution
              </p>
              <p className="text-[var(--color-muted)] leading-relaxed">
                Creates an iPad purchase, freezes receipt, triggers condition drift, and locks escrow settlement until operator correction.
              </p>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <Button
              variant="primary"
              size="md"
              icon={<Play className="w-4 h-4 fill-current" />}
              loading={isRunningDemo}
              onClick={handleRunDemo}
              className="w-full justify-center text-[14px]"
            >
              Run Instant Demo Scenario →
            </Button>
            <div className="flex items-center justify-center pt-1 text-[13px]">
              <button
                type="button"
                onClick={() => navigate('/proof')}
                className="text-[var(--color-muted)] hover:text-[var(--color-ink)] transition-colors cursor-pointer"
              >
                View verification proof & metrics →
              </button>
            </div>
          </div>
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
                Click <strong>Run Instant Demo Scenario</strong> (Lane 2) or launch the real flow with the Shopper Agent (Lane 1).
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
                Use the <strong>Scenario console</strong> on the receipt to trigger a refurbished item mismatch.
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
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[12px] font-mono">
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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[14px]">
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
              Warehouse order-line pick events and carrier tracking scans (UPS/FedEx) are generated by the Scenario console test harness.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

