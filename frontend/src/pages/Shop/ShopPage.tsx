import React, { useState } from 'react'
import { useNavigate } from 'react-router'
import { Stepper } from '../../components/domain/Stepper'
import { Card } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { FormField } from '../../components/ui/FormField'
import { Badge } from '../../components/ui/Badge'
import { HashChip } from '../../components/ui/HashChip'
import { PayPalAuthorizeButton } from '../../components/domain/PayPalAuthorizeButton'
import { api } from '../../lib/api'
import { formatMinor } from '../../lib/money'
import { sha256Hex, canonicalJson, truncateHash } from '../../lib/hash'
import type { IntentConstraints, ProductCandidate, MerchantQuote } from '../../types/api'
import { Check, AlertCircle, ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react'

const STEPS = [
  { id: 1, title: 'Instruction' },
  { id: 2, title: 'Constraints' },
  { id: 3, title: 'Candidates' },
  { id: 4, title: 'Merchant quote' },
  { id: 5, title: 'Review & approve' },
  { id: 6, title: 'Authorize' },
]

export const ShopPage: React.FC = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)

  // Step 1: Instruction
  const [instruction, setInstruction] = useState(
    'Find new black over-ear wireless noise cancelling headphones under $100 delivered within 5 days'
  )
  const [isExtracting, setIsExtracting] = useState(false)

  // Step 2: Constraints
  const [constraints, setConstraints] = useState<IntentConstraints | null>(null)
  const [isFallback, setIsFallback] = useState(false)

  // Step 3: Candidates
  const [candidates, setCandidates] = useState<ProductCandidate[]>([])
  const [selectedProduct, setSelectedProduct] = useState<ProductCandidate | null>(null)
  const [selectedColor, setSelectedColor] = useState('Black')
  const [isSearching, setIsSearching] = useState(false)

  // Step 4: Quote
  const [quote, setQuote] = useState<MerchantQuote | null>(null)
  const [isQuoting, setIsQuoting] = useState(false)

  // Step 5: Approve
  const [receiptHash, setReceiptHash] = useState<string | null>(null)
  const [isApproved, setIsApproved] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [createdPurchaseId, setCreatedPurchaseId] = useState<string | null>(null)

  // Step 6: Authorization result
  const [authData, setAuthData] = useState<{ orderId: string; authorizationId: string } | null>(null)

  // Handlers
  const handleExtractConstraints = async () => {
    setIsExtracting(true)
    try {
      const res = await api.extractConstraints(instruction)
      setConstraints(res)
      setCurrentStep(2)
    } catch {
      setIsFallback(true)
    } finally {
      setIsExtracting(false)
    }
  }

  const handleSearchCandidates = async () => {
    if (!constraints) return
    setIsSearching(true)
    try {
      const res = await api.searchCandidates(constraints)
      setCandidates(res)
      if (res.length > 0) {
        setSelectedProduct(res[0])
        setSelectedColor(res[0].variants[0] || 'Black')
      }
      setCurrentStep(3)
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectProduct = async (prod: ProductCandidate) => {
    setSelectedProduct(prod)
    setIsQuoting(true)
    try {
      const q = await api.getQuote(prod)
      setQuote(q)
      setCurrentStep(4)
    } finally {
      setIsQuoting(false)
    }
  }

  const handlePrepareReceipt = async () => {
    if (!constraints || !selectedProduct || !quote) return

    const terms = {
      buyer_instruction: instruction,
      constraints,
      product_snapshot: { ...selectedProduct, selected_variant: selectedColor },
      merchant_quote: quote,
      capture_conditions: {
        strict_condition_match: true,
        require_carrier_acceptance: true,
        max_total_cents: constraints.max_total_cents,
        currency: 'USD',
      },
    }

    const hash = `sha256:${await sha256Hex(canonicalJson(terms))}`
    setReceiptHash(hash)
    setCurrentStep(5)
  }

  const handleApproveReceipt = async () => {
    if (!receiptHash) return
    setIsApproving(true)
    try {
      // Create and approve in demo backend
      const res = await api.runDemoScenario(instruction)
      setCreatedPurchaseId(res.purchase_id)
      setIsApproved(true)
      setCurrentStep(6)
    } finally {
      setIsApproving(false)
    }
  }

  const isContractRejected = quote && constraints && quote.total_cents > constraints.max_total_cents

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-[var(--color-line)] pb-4">
        <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
          AGENTIC COMMERCE INTERFACE
        </p>
        <h1 className="text-[28px] font-semibold text-[var(--color-ink)]">Shopper agent flow</h1>
        <p className="text-[14px] text-[var(--color-muted)] mt-0.5">
          Step 1 through Step 6: Buyer instruction, constraint freezing, receipt approval, and PayPal authorization hold.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-start gap-8">
        {/* Left: Stepper rail (240px) */}
        <Stepper
          steps={STEPS}
          currentStep={currentStep}
          onStepSelect={(s) => setCurrentStep(s)}
          locked={isApproved}
        />

        {/* Center: Step content (flex) */}
        <div className="flex-1 w-full min-w-0">
          {/* STEP 1 */}
          {currentStep === 1 && (
            <Card title="Step 1: Buyer Instruction" subtitle="Describe the product and delivery limits you require">
              <div className="space-y-4">
                <FormField
                  id="instruction-text"
                  label="Natural language request"
                  hint="Relative dates like '5 days' are resolved by the server clock, not the AI"
                >
                  <textarea
                    id="instruction-text"
                    rows={4}
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                    className="w-full p-3 bg-white border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px] text-[var(--color-ink)] focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2 leading-relaxed"
                  />
                </FormField>

                <div className="flex justify-end pt-2">
                  <Button
                    variant="primary"
                    loading={isExtracting}
                    onClick={handleExtractConstraints}
                    icon={<ArrowRight className="w-4 h-4" />}
                  >
                    Extract constraints
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* STEP 2 */}
          {currentStep === 2 && constraints && (
            <Card
              title="Step 2: Review & Edit Constraints"
              subtitle="Frozen constraints become binding conditions on the merchant settlement"
              action={
                <Badge tone={isFallback ? 'neutral' : 'info'}>
                  {isFallback ? 'Fallback parser' : 'AI extracted'}
                </Badge>
              }
            >
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField id="c-type" label="Product type">
                    <input
                      id="c-type"
                      type="text"
                      value={constraints.product_type}
                      onChange={(e) => setConstraints({ ...constraints, product_type: e.target.value })}
                      className="w-full h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px]"
                    />
                  </FormField>

                  <FormField id="c-cond" label="Condition">
                    <select
                      id="c-cond"
                      value={constraints.condition}
                      onChange={(e) => setConstraints({ ...constraints, condition: e.target.value })}
                      className="w-full h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px] bg-white"
                    >
                      <option value="New">New</option>
                      <option value="Used">Used</option>
                      <option value="Refurbished">Refurbished</option>
                    </select>
                  </FormField>

                  <FormField id="c-variant" label="Preferred color / variant">
                    <input
                      id="c-variant"
                      type="text"
                      value={constraints.variant_color}
                      onChange={(e) => setConstraints({ ...constraints, variant_color: e.target.value })}
                      className="w-full h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px]"
                    />
                  </FormField>

                  <FormField id="c-max" label="Max budget (USD)">
                    <input
                      id="c-max"
                      type="number"
                      value={constraints.max_total_cents / 100}
                      onChange={(e) =>
                        setConstraints({
                          ...constraints,
                          max_total_cents: Math.round(parseFloat(e.target.value || '0') * 100),
                        })
                      }
                      className="w-full h-10 px-3 border border-[var(--color-line-strong)] rounded-[var(--radius-control)] text-[14px]"
                    />
                  </FormField>
                </div>

                <div className="p-3 bg-[var(--color-inset)] rounded-[var(--radius-control)] text-[14px] text-[var(--color-muted)]">
                  Deadline resolved: <strong className="text-[var(--color-ink)]">{constraints.resolved_deadline_at.slice(0, 10)}</strong> (from server clock +{constraints.deadline_days} days)
                </div>

                <div className="flex items-center justify-between pt-2">
                  <Button variant="secondary" onClick={() => setCurrentStep(1)} icon={<ArrowLeft className="w-4 h-4" />}>
                    Back
                  </Button>
                  <Button
                    variant="primary"
                    loading={isSearching}
                    onClick={handleSearchCandidates}
                    icon={<ArrowRight className="w-4 h-4" />}
                  >
                    Search products
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* STEP 3 */}
          {currentStep === 3 && (
            <Card title="Step 3: Discovered Candidates" subtitle="Select the exact catalog item and variant">
              <div className="space-y-4">
                <div className="divide-y divide-[var(--color-line)]">
                  {candidates.map((prod) => (
                    <div
                      key={prod.id}
                      onClick={() => setSelectedProduct(prod)}
                      className={`p-4 rounded-[var(--radius-control)] border transition-all cursor-pointer mb-2 ${
                        selectedProduct?.id === prod.id
                          ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)]/20 ring-1 ring-[var(--color-accent)]'
                          : 'border-[var(--color-line)] bg-white hover:bg-[var(--color-inset)]'
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <img
                          src={prod.image_url}
                          alt={prod.title}
                          className="w-12 h-12 rounded object-cover border border-[var(--color-line)] shrink-0 bg-white"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <h3 className="text-[14px] font-semibold text-[var(--color-ink)] truncate">{prod.title}</h3>
                            <span className="text-[18px] font-semibold tabular-nums text-[var(--color-ink)]">
                              {formatMinor(prod.price_cents, prod.currency)}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                            <span className="text-[12px] text-[var(--color-muted)]">{prod.brand}</span>
                            <span>·</span>
                            <span className="text-[12px] text-[var(--color-muted)]">{prod.merchant_domain}</span>
                            <span>·</span>
                            {prod.condition ? (
                              <Badge tone="ok">{prod.condition}</Badge>
                            ) : (
                              <Badge tone="warn">UNVERIFIED</Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      {selectedProduct?.id === prod.id && (
                        <div className="mt-4 pt-3 border-t border-[var(--color-line)] flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-[12px] font-semibold text-[var(--color-ink)]">Variant color:</span>
                            {prod.variants.map((v) => (
                              <label key={v} className="inline-flex items-center gap-1.5 text-[14px] cursor-pointer">
                                <input
                                  type="radio"
                                  name="color"
                                  checked={selectedColor === v}
                                  onChange={() => setSelectedColor(v)}
                                  className="text-[var(--color-accent)] focus:ring-[var(--color-accent)]"
                                />
                                <span>{v}</span>
                              </label>
                            ))}
                          </div>
                          <Button
                            variant="primary"
                            size="sm"
                            loading={isQuoting}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSelectProduct(prod)
                            }}
                          >
                            Select offer
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <p className="text-[12px] text-[var(--color-muted)]">
                  Raw snapshot is hashed and stored permanently upon selection.
                </p>
              </div>
            </Card>
          )}

          {/* STEP 4 */}
          {currentStep === 4 && quote && selectedProduct && (
            <Card title="Step 4: Merchant Quote Confirmation" subtitle="Checkout total confirmed independently from catalog listing">
              <div className="space-y-4">
                <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-inset)] border border-[var(--color-line)] space-y-2.5">
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[var(--color-muted)]">Seller</span>
                    <span className="font-semibold text-[var(--color-ink)]">{quote.seller_name}</span>
                  </div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[var(--color-muted)]">Domain validation</span>
                    <span className="font-mono text-[12px] text-[var(--color-ink)]">{quote.seller_domain}</span>
                  </div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[var(--color-muted)]">Subtotal</span>
                    <span className="tabular-nums font-semibold">{formatMinor(quote.subtotal_cents)}</span>
                  </div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[var(--color-muted)]">Shipping</span>
                    <span className="tabular-nums font-semibold">{formatMinor(quote.shipping_cents)}</span>
                  </div>
                  <div className="flex justify-between text-[14px]">
                    <span className="text-[var(--color-muted)]">Tax</span>
                    <span className="tabular-nums font-semibold">{formatMinor(quote.tax_cents)}</span>
                  </div>
                  <div className="h-[1px] bg-[var(--color-line)] my-1" />
                  <div className="flex justify-between text-[18px] font-semibold">
                    <span>Confirmed total</span>
                    <span className="text-[18px] text-[var(--color-ink)] tabular-nums">
                      {formatMinor(quote.total_cents)} USD
                    </span>
                  </div>
                </div>

                <p className="text-[12px] text-[var(--color-muted)]">
                  Sandbox stand-in for {quote.seller_domain}. Checkout total confirmed separately from catalog price.
                </p>

                <div className="flex items-center justify-between pt-2">
                  <Button variant="secondary" onClick={() => setCurrentStep(3)} icon={<ArrowLeft className="w-4 h-4" />}>
                    Back
                  </Button>
                  <Button variant="primary" onClick={handlePrepareReceipt} icon={<ArrowRight className="w-4 h-4" />}>
                    Compile Promise Receipt
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {/* STEP 5 */}
          {currentStep === 5 && receiptHash && quote && constraints && (
            <Card title="Step 5: Review & Approve Receipt" subtitle="Cryptographic snap of all buyer constraints and checkout terms">
              <div className="space-y-4">
                {isContractRejected ? (
                  <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-bad-soft)] border border-[var(--color-bad-line)] space-y-2">
                    <p className="text-[14px] font-semibold text-[var(--color-bad)] flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" /> Contract rejected
                    </p>
                    <p className="text-[14px] text-[var(--color-bad)]">
                      Merchant quote total ({formatMinor(quote.total_cents)}) exceeds your approved limit of (
                      {formatMinor(constraints.max_total_cents)}). No PayPal authorization request was allowed.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="p-4 rounded-[var(--radius-control)] border border-[var(--color-line)] bg-white space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-muted)]">
                          Cryptographic Receipt Hash
                        </span>
                        <HashChip value={receiptHash} kind="sha" />
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[14px]">
                        <div>
                          <span className="text-[var(--color-muted)]">Item:</span>{' '}
                          <span className="font-semibold">{selectedProduct?.title}</span>
                        </div>
                        <div>
                          <span className="text-[var(--color-muted)]">Condition constraint:</span>{' '}
                          <span className="font-semibold text-[var(--color-ok)]">{constraints.condition}</span>
                        </div>
                        <div>
                          <span className="text-[var(--color-muted)]">Variant:</span>{' '}
                          <span className="font-semibold">{selectedColor}</span>
                        </div>
                        <div>
                          <span className="text-[var(--color-muted)]">Total:</span>{' '}
                          <span className="font-semibold">{formatMinor(quote.total_cents)} USD</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-2">
                      <Button variant="secondary" onClick={() => setCurrentStep(4)} icon={<ArrowLeft className="w-4 h-4" />}>
                        Back
                      </Button>
                      <Button
                        variant="primary"
                        loading={isApproving}
                        onClick={handleApproveReceipt}
                        icon={<ShieldCheck className="w-4 h-4" />}
                      >
                        Approve receipt {truncateHash(receiptHash)}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* STEP 6 */}
          {currentStep === 6 && quote && receiptHash && (
            <Card title="Step 6: Authorize PayPal Hold" subtitle="Place authorization hold. Zero money moves until fulfillment verification passes.">
              <div className="space-y-6">
                <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-warn-soft)]/50 border border-[var(--color-warn-line)]">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[12px] font-semibold uppercase tracking-[0.04em] text-[var(--color-warn)]">
                        Authorization Amount
                      </p>
                      <p className="text-[28px] font-semibold tabular-nums text-[var(--color-ink)]">
                        {formatMinor(quote.total_cents)} <span className="text-[18px] text-[var(--color-muted)]">USD</span>
                      </p>
                    </div>
                    <Badge tone="warn">Authorized · not captured</Badge>
                  </div>
                </div>

                {!authData ? (
                  <div className="py-2">
                    <PayPalAuthorizeButton
                      receiptId={createdPurchaseId || 'demo'}
                      amountCents={quote.total_cents}
                      receiptHash={receiptHash}
                      onAuthorized={(data) => setAuthData(data)}
                    />
                  </div>
                ) : (
                  <div className="p-4 rounded-[var(--radius-control)] bg-[var(--color-ok-soft)] border border-[var(--color-ok-line)] space-y-4">
                    <div className="flex items-center gap-2 text-[var(--color-ok)]">
                      <Check className="w-5 h-5 font-bold" />
                      <span className="font-semibold text-[14px]">PayPal Sandbox Authorization Created</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[12px] font-mono">
                      <div>
                        <span className="text-[var(--color-muted)]">Order ID:</span> {authData.orderId}
                      </div>
                      <div>
                        <span className="text-[var(--color-muted)]">Authorization ID:</span> {authData.authorizationId}
                      </div>
                    </div>

                    <p className="text-[14px] text-[var(--color-ink)]">
                      Funds are held securely. Control is transferred to the PromiseLoop drift engine.
                    </p>

                    <Button
                      variant="primary"
                      onClick={() => navigate(`/receipts/${createdPurchaseId}`)}
                      icon={<ArrowRight className="w-4 h-4" />}
                    >
                      Open promise receipt
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>

        {/* Right: Promise summary column (320px sticky) */}
        <div className="w-full lg:w-80 shrink-0 sticky top-24 space-y-4">
          <Card padding="md" title="Promise so far" subtitle="Summary of buyer constraints">
            <div className="space-y-3 text-[14px] mt-2">
              <div className="flex justify-between">
                <span className="text-[var(--color-muted)]">Product</span>
                <span className="font-semibold text-right max-w-[160px] truncate">
                  {selectedProduct ? selectedProduct.title : constraints?.product_type || '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-muted)]">Condition</span>
                <span className="font-semibold">{constraints?.condition || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-muted)]">Max budget</span>
                <span className="font-semibold tabular-nums">
                  {constraints ? formatMinor(constraints.max_total_cents) : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-muted)]">Deadline</span>
                <span className="font-semibold">
                  {constraints ? constraints.resolved_deadline_at.slice(0, 10) : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-muted)]">Receipt hash</span>
                <span className="font-mono text-[12px] truncate max-w-[140px]">
                  {receiptHash ? truncateHash(receiptHash) : '—'}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

