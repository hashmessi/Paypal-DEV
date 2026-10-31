Three-loop product hardening: PromiseLoop
=========================================

Final direction: Agentic commerce accountability

My first major correction: the previous PromiseLoop concept was still too close to existing products.

The initial version was essentially an AI agent that detects an order problem, recommends a refund, and calls PayPal. That is not sufficiently differentiated.

I found a more fundamental issue in the competitive landscape.

*   Gorgias Help Center+1
    
*   AfterShip Help Center+1
    
*   AI-Driven Tracking & Notification+1
    
*   Devpost
    

Therefore, we should not compete by building another customer-support agent, shipping tracker, refund bot, or payment firewall.

The strategic gap
-----------------

PayPal's own agentic-commerce discussion identifies the need for post-purchase experiences, including returns and disputes, alongside discovery and checkout.

newsroom.paypal-corp.com+1

But there is a crucial distinction between:

1.  What a buyer originally instructed an AI agent to purchase.
    
2.  What product and terms the agent selected.
    
3.  What the merchant promised.
    
4.  What PayPal actually charged.
    
5.  What the merchant ultimately fulfilled.
    
6.  Whether the final outcome satisfied the original instruction.
    

These facts live in different records and systems.

The product opportunity is to connect that entire chain and detect when the actual purchase outcome diverges from the original authorized intent.

That is a stronger direction than generic refund automation.

Loop 1 — Senior product developer
=================================

Question: What should we actually build that has a technically meaningful core?

PromiseLoop
===========

### The accountability layer for AI-initiated commerce.

Tagline: Every AI purchase should have a verifiable promise—and every broken promise should have a controlled resolution.

[PanthereAI — AI Agent Governance, Security & Risk Management](https://images.openai.com/static-rsc-4/FPic8FGdNr5yZnJSVs9MyJKpnbA1UVwjbdvxjx1l_7KDUmB0bOn5XFr9wDQLukB-6yOYaCZm8ZsqGGY9BkdiugoQq18KZQT90Ar12xyDboOSUcqMBrhOg8TebLrhy3gRfiu7jnI9KWzMXQG7DZQZ_ba519TPR91UAe1zcpaWqrg?purpose=inline)[panthere.ai](https://panthere.ai/?utm_source=chatgpt.com)

1.1 Product definition
----------------------

PromiseLoop is an AI-powered purchase accountability system that preserves the shopper's original intent, binds it to the selected product and merchant commitment, links it to an actual PayPal transaction, and checks whether the final outcome fulfills that commitment.

When a mismatch occurs, it produces an evidence-backed resolution plan and controls the resulting payment action.

The product's central entity is not a support ticket or a refund request.

It is an Intent-to-Outcome Contract.

This is a structured, versioned record of what the human authorized and what subsequently happened.

1.2 The signature feature: Promise Receipt
------------------------------------------

Core differentiator

Every purchase gets a Promise Receipt before money moves.

Promise Receipt — PL-00842
--------------------------

PURCHASE INTENT

Approved by buyer

Original user instruction

"Find new black wireless headphones, over-ear, under $100, delivered by November 5. No refurbished products."

Frozen purchase constraints

Constraint

Authorized value

Product

Selected product ID

Condition

New

Variant

Black

Maximum total

$100

Delivery deadline

Nov 5

Substitution

Not allowed

Commercial commitment

Selected merchant

Demo Merchant A

Approved purchase

$89.99

Promised delivery

November 5

PayPal binding

PayPal order

ORDER-XXXX

Capture status

Captured

EXAMPLE DEMONSTRATION DATA

### This is the contract against which the outcome will be checked.

Why is this valuable?

A normal checkout receipt proves a transaction happened. A Promise Receipt preserves the conditions under which the buyer authorized the transaction.

A receipt alone does not prove the merchant fulfilled the agreement. PromiseLoop uses subsequent evidence to evaluate that separately.

1.3 The unique technical capability: Promise Drift Engine
---------------------------------------------------------

This is the product's centerpiece.

The engine continuously compares four states:

State

What it represents

Intent state

What the buyer authorized

Commercial state

What the merchant selected and promised

Financial state

What PayPal actually processed

Fulfillment state

What happened to the order

It detects divergence across these states.

Examples:

*   Product variant purchased differs from the authorized variant.
    
*   Captured total exceeds the buyer's approved maximum.
    
*   Merchant confirms a delivery date later than the authorized deadline.
    
*   Order fulfillment reports a substituted item.
    
*   Customer reports a missing item while the fulfillment record reports a completed order.
    
*   Refund requested, but PayPal's actual transaction status does not reflect completion.
    

The system must distinguish a verified mismatch from an unverified allegation.

1.4 The signature demonstration: Promise Replay
-----------------------------------------------

[Dexter: AI-powered Procure-to-Pay](https://images.openai.com/static-rsc-4/7fQ2eZXw9iIzf6QYvIQJ87NpeQHL2xLsvoHR1xueOx5jejzaVeh2Fw_v75yeTaHnNReIhPMEu4yif6EPZcxXsYqCed8jW_nyLTqz0vvWPgOBl9BQutC3NfO1r74MMIEI1_ZX6vPIpEGii-qtJXNnAEkxF1fHfh_1Fl-GwfzWP64?purpose=inline)[getdexter.co](https://www.getdexter.co/?utm_source=chatgpt.com)

A judge should be able to select one purchase and click Replay Promise.

The screen reveals:

1.  Original buyer instruction.
    
2.  Product discovered using Channel3.
    
3.  Exact product and variant selected.
    
4.  Merchant commitment recorded.
    
5.  User approval.
    
6.  PayPal order and capture.
    
7.  Fulfillment event.
    
8.  Detected deviation.
    
9.  Recommended remedy.
    
10.  Actual PayPal outcome.
    

The judge can see precisely where the purchase diverged.

This is not an ordinary chat history. It is an auditable reconstruction of the purchase lifecycle.

1.5 Technical invariants
------------------------

The engine must enforce:

Invariant

Enforcement

Product integrity

Actual item must match the approved product and variant

Spending integrity

Captured purchase must not exceed approved total

Merchant integrity

Merchant must match the authorized seller

Promise integrity

Actual fulfillment must be evaluated against the recorded commitment

Evidence integrity

A changed commitment must invalidate affected validations

Financial integrity

Refund cannot exceed remaining refundable amount

Execution integrity

Repeated requests cannot create duplicate financial actions

Decision integrity

AI cannot independently modify authorized constraints

The important architectural principle: the LLM interprets evidence; deterministic code controls money.

Loop 1 — Senior product developer: the critical architectural upgrade
=====================================================================

The original version used:

AI recommendation → Human approval → PayPal refund

That is backward for this product. It lets money move first and attempts to repair the problem afterward.

The stronger approach is:

Buyer intent → PayPal authorization → Fulfillment verification → Conditional capture

Major upgrade Promise-Gated Settlement

PayPal already supports authorizing a payment and capturing it later. Its documentation explicitly describes charging after an order is shipped. An authorization holds the buyer's funds without transferring them to the merchant. The normal honor period is three days, with authorizations potentially valid for up to 29 days depending on the conditions and reauthorization.

PayPal Developer+1

This gives PromiseLoop a meaningful financial mechanism rather than another refund API wrapper.

1.6 The actual PayPal transaction flow
--------------------------------------

Step 1 — User approves purchase

Approved

The buyer sees the exact product, total, merchant, promised shipment/delivery terms and conditions for capturing payment.

Step 2 — PayPal authorizes

Not captured

Orders v2 with AUTHORIZE. Store the order ID and authorization ID. This is a payment authorization, not an escrow.

Step 3 — Fulfillment evidence arrives

Verifying

The fulfillment adapter receives the order line/SKU and a carrier-accepted shipping event.

Step 4 — Promise Drift Engine

Match required

Compare the authorized item, variant, price and merchant promise against the fulfillment evidence.

MATCH

Capture authorized payment.

DRIFT

Block capture; request review.

Step 5 — Financial outcome

Capture when conditions pass, or void an unfulfillable authorization when appropriate. A captured transaction requires a refund rather than a void.

The relevant PayPal endpoints are:

Operation

API

Create purchase

Orders v2

Authorize funds

Orders v2 authorization

Capture authorized funds

POST /v2/payments/authorizations/{id}/capture

Cancel authorization

POST /v2/payments/authorizations/{id}/void

Refund after capture

POST /v2/payments/captures/{id}/refund

Verify asynchronous events

PayPal Webhooks

PayPal Developer+4

Two important constraints:

*   An authorization is not escrow and does not independently prove the merchant's fulfillment claim.
    
*   Payment capture must be governed by buyer-approved conditions and reliable fulfillment evidence. The initial MVP should use in-stock orders capable of shipping within the normal authorization honor period. Do not build a preorder system around an authorization that may expire.
    

The real innovation is not delayed capture itself. PayPal already offers that. It is using an AI-derived, human-approved purchase contract to determine exactly when capture is permitted.

Loop 2 — Strategic product analyst
==================================

Question: Does this solve a real problem, and is it different enough to deserve attention?

2.1 The competitive boundary
----------------------------

This is where we must be particularly strict.

Existing solution

What it already does

What PromiseLoop must own

Gorgias

Post-purchase customer support, actions, returns

Buyer-intent-to-fulfillment verification

AfterShip

Shipment tracking and exception detection

Purchase-contract conditions governing PayPal capture

Narvar

Delivery promises, communications and returns

Immutable authorization-to-outcome record

Warden

Agent payment permissions, security and audit

Semantic purchase fulfillment and conditional settlement

Agentic Cart / PayPilot

AI discovery and PayPal checkout

Verification after checkout but before settlement

Sources:

Gorgias Help Center+5

We must not claim none of these companies could implement this capability. We have identified a specific product distinction, not proven an exclusive market.

### The gap

The missing connection
----------------------

Buyer intent

What the user actually authorized

Merchant promise

What the seller committed to

PayPal payment

What was authorized and captured

Actual outcome

What fulfillment records show

PromiseLoop joins all four into one verifiable lifecycle.

This is a particularly interesting emerging problem because the PayPal agentic-commerce strategy itself identifies post-purchase returns and disputes as necessary parts of agentic commerce.

newsroom.paypal-corp.com+1

However, the available evidence supports the strategic relevance of the problem more strongly than the current commercial demand.

We still need to validate whether agent-platform operators and merchants will pay for this specific capability.

2.2 Who exactly needs PromiseLoop?
----------------------------------

Do not market the MVP to everyone.

Primary target user: a commerce platform operator or merchant adopting AI shopping agents and responsible for ensuring those agents fulfil buyer-approved purchase conditions.

Their problem:

"When an AI agent buys something for my customer, I need to know that the exact item, price and agreed conditions were respected before I settle the payment."

This is substantially more specific than "merchants want better customer support."

2.3 What outcome can we measure?
--------------------------------

The product needs metrics that reflect its actual job.

Metric

What to demonstrate

Contract violation detection

How many seeded mismatches are detected

Unsafe capture prevention

How many mismatched orders are prevented from capture

False block rate

How often valid orders are incorrectly held

Capture decision latency

Time from verified fulfillment event to decision

Duplicate action prevention

Whether repeated events produce duplicate captures

Authorization expiry handling

Whether an expiring authorization is correctly escalated

Use a labeled dataset of approximately 15–20 scenarios, including valid purchases, invalid variants, price mismatches, seller substitutions, late shipment forecasts and replayed events.

Do not claim a real-world chargeback reduction. The MVP can demonstrate that it prevents specified contract violations from reaching payment capture.

2.4 The dangerous assumptions to eliminate
------------------------------------------

Assumption

Correction

Channel3 knows the final merchant checkout price

Obtain the actual checkout quote separately

The AI knows whether a product was physically shipped

Require fulfillment evidence from an integration or clearly labeled simulator

A carrier label means the carrier received the item

Require an accepted/carrier-scan event

A seller's own shipping claim proves fulfillment

Treat merchant claims as lower-trust evidence

PayPal authorization is escrow

Explain the difference between authorization and settlement

AI can approve payments independently

Deterministic rules and explicitly authorized conditions control capture

Every merchant supports delayed capture

Restrict the first implementation to an eligible PayPal merchant flow

Loop 2 conclusion: PromiseLoop has a credible emerging problem and a defensible product boundary. Its impact must be demonstrated through actual contract violations and their financial consequences, not general claims about AI commerce.

Loop 3 — Final hackathon judge
==============================

Question: Does the product distinguish itself, use PayPal meaningfully, and make a compelling demonstration?

The official rubric has five equally weighted criteria.

Devpost

Here is the judge-facing product target.

Category

Target

Evidence required

Technological implementation

9/10

Real authorization, capture, void, Channel3 calls, AI constraint extraction, signed receipt and verified webhooks

Design

9/10

Clean purchase approval and a single Promise Replay interface with clear state transitions

Potential impact

8/10

Explicit target user, measurable blocked violations, meaningful operational use case

Innovation

9/10

Purchase intent compiled into conditions that govern PayPal settlement after fulfillment

Presentation

10/10

One continuous mismatch → blocked capture → corrected evidence → actual capture demonstration

These are implementation targets, not pre-awarded points.

3.1 The judge's six likely objections
-------------------------------------

Objection 1: "Isn't this just PayPal's authorize-and-capture feature?"

No. PayPal supplies the payment lifecycle. PromiseLoop creates the typed buyer-intent contract and the evidence-validation engine that determines when capture conditions are satisfied.

Objection 2: "Why do you need AI?"

Because buyers express constraints in natural language, while product listings, merchant promises and fulfillment records are structured differently. AI translates and explains these records. Deterministic logic performs exact matching and financial authorization.

Objection 3: "How do you prove what actually shipped?"

The prototype accepts merchant fulfillment data and a carrier-accepted event. These are recorded with source, timestamp and confidence. The demo must disclose that the carrier simulator is synthetic. A production integration would require authenticated merchant and carrier events.

Objection 4: "What happens when the merchant cannot fulfil?"

PromiseLoop does not capture the authorization when the approved conditions fail. Where permitted and appropriate, it voids the authorization and records the outcome.

Objection 5: "What happens when authorization expires?"

The engine tracks authorization timing and requires the applicable reauthorization workflow or a fresh approval. It must never assume that an expired authorization remains available for capture.

Objection 6: "Why wouldn't a merchant simply use a normal payment gateway?"

A conventional gateway can process authorization and capture. PromiseLoop adds the purchase-specific constraint and fulfillment verification process needed for a merchant or agent platform to enforce an approved commitment. Whether that earns a separate software budget requires market validation.

3.2 The demo must be this exact scenario
----------------------------------------

Recommended final demo

Act 1 — The shopper's instruction
---------------------------------

"Buy new black over-ear headphones under $100. No refurbished items. Ship in time for my November 5 deadline."

AI extracts typed constraints.

Act 2 — Actual product discovery
--------------------------------

Channel3 searches real product data and returns candidates. The buyer chooses the exact product and variant.

The merchant offer and full checkout total are separately confirmed.

Act 3 — The Promise Receipt
---------------------------

PromiseLoop freezes the selected product, variant, price limit, seller and fulfillment conditions. The buyer approves the exact contract.

Tamper-evident receipt hash is generated.

Act 4 — PayPal authorization
----------------------------

$89.99
======

Authorized, not capturedThe buyer approves the PayPal Sandbox authorization.

Act 5 — The mismatch
--------------------

The simulated merchant fulfillment record says the product picked is refurbished.

PROMISE VIOLATION

Authorized: New product

Fulfillment: Refurbished product

CAPTURE BLOCKED
---------------

The original authorization is not settled.

Act 6 — Correction
------------------

The seller corrects the fulfillment record. The exact SKU is confirmed and an accepted carrier event is received.

Act 7 — Promise verified
------------------------

All capture conditions passed

PromiseLoop executes the authorized capture using PayPal. The transaction response and subsequent verified event are recorded in the Promise Receipt.

Act 8 — Replay
--------------

The complete sequence from original instruction to actual payment settlement is visible in one audit timeline.

This demonstration contains an actual product search, an AI-derived purchase contract, a real PayPal authorization, a meaningful negative case, deterministic re-evaluation and a real PayPal capture.

It is much harder to dismiss than an agent that just creates a PayPal order from a chat prompt.

4\. Final locked product architecture
=====================================

4.1 System components
---------------------

#chatgpt-mermaid-\_r\_rg\_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(237, 237, 237);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-\_r\_rg\_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r\_rg\_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-\_r\_rg\_ .error-icon{fill:rgb(48, 48, 48);}#chatgpt-mermaid-\_r\_rg\_ .error-text{fill:rgb(237, 237, 237);stroke:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-\_r\_rg\_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-\_r\_rg\_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-\_r\_rg\_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-\_r\_rg\_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-\_r\_rg\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r\_rg\_ .marker.cross{stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r\_rg\_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-\_r\_rg\_ p{margin:0;}#chatgpt-mermaid-\_r\_rg\_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .cluster-label text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .cluster-label span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-\_r\_rg\_ .label text,#chatgpt-mermaid-\_r\_rg\_ span{fill:rgb(237, 237, 237);color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .node rect,#chatgpt-mermaid-\_r\_rg\_ .node circle,#chatgpt-mermaid-\_r\_rg\_ .node ellipse,#chatgpt-mermaid-\_r\_rg\_ .node polygon,#chatgpt-mermaid-\_r\_rg\_ .node path{fill:rgb(9, 23, 44);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .rough-node .label text,#chatgpt-mermaid-\_r\_rg\_ .node .label text,#chatgpt-mermaid-\_r\_rg\_ .image-shape .label,#chatgpt-mermaid-\_r\_rg\_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-\_r\_rg\_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .rough-node .label,#chatgpt-mermaid-\_r\_rg\_ .node .label,#chatgpt-mermaid-\_r\_rg\_ .image-shape .label,#chatgpt-mermaid-\_r\_rg\_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-\_r\_rg\_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-\_r\_rg\_ .root .anchor path{fill:rgb(175, 175, 175)!important;stroke-width:0;stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r\_rg\_ .arrowheadPath{fill:rgb(175, 175, 175);}#chatgpt-mermaid-\_r\_rg\_ .edgePath .path{stroke:rgb(175, 175, 175);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .flowchart-link{stroke:rgb(175, 175, 175);fill:none;}#chatgpt-mermaid-\_r\_rg\_ .edgeLabel{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r\_rg\_ .edgeLabel p{background-color:rgb(0, 0, 0);}#chatgpt-mermaid-\_r\_rg\_ .edgeLabel rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r\_rg\_ .labelBkg{background-color:rgba(0, 0, 0, 0.5);}#chatgpt-mermaid-\_r\_rg\_ .cluster rect{fill:rgb(48, 48, 48);stroke:rgba(255, 255, 255, 0.15);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .cluster text{fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ .cluster span{color:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(48, 48, 48);border:1px solid rgba(255, 255, 255, 0.15);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-\_r\_rg\_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(237, 237, 237);}#chatgpt-mermaid-\_r\_rg\_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-\_r\_rg\_ .icon-shape,#chatgpt-mermaid-\_r\_rg\_ .image-shape{background-color:rgb(0, 0, 0);text-align:center;}#chatgpt-mermaid-\_r\_rg\_ .icon-shape p,#chatgpt-mermaid-\_r\_rg\_ .image-shape p{background-color:rgb(0, 0, 0);padding:2px;}#chatgpt-mermaid-\_r\_rg\_ .icon-shape .label rect,#chatgpt-mermaid-\_r\_rg\_ .image-shape .label rect{opacity:0.5;background-color:rgb(0, 0, 0);fill:rgb(0, 0, 0);}#chatgpt-mermaid-\_r\_rg\_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-\_r\_rg\_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-\_r\_rg\_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node rect,#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].cluster rect,#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node polygon{stroke:url(#chatgpt-mermaid-\_r\_rg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node path{stroke:url(#chatgpt-mermaid-\_r\_rg\_-gradient);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node circle{stroke:url(#chatgpt-mermaid-\_r\_rg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].node circle .state-start{fill:#000000;}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].icon-shape .icon{fill:url(#chatgpt-mermaid-\_r\_rg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r\_rg\_ \[data-look="neo"\].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-\_r\_rg\_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-\_r\_rg\_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r\_rg\_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-\_r\_rg\_ .node tspan\[font-weight="normal"\],#chatgpt-mermaid-\_r\_rg\_ .edgeLabels tspan\[font-weight="normal"\]{font-weight:600;}#chatgpt-mermaid-\_r\_rg\_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .node rect,#chatgpt-mermaid-\_r\_rg\_ .node circle,#chatgpt-mermaid-\_r\_rg\_ .node ellipse,#chatgpt-mermaid-\_r\_rg\_ .node polygon,#chatgpt-mermaid-\_r\_rg\_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-\_r\_rg\_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-\_r\_rg\_ .mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-\_r\_rg\_ .edgePaths .flowchart-link{stroke:rgb(175, 175, 175);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-\_r\_rg\_ .marker{fill:rgb(175, 175, 175);stroke:rgb(175, 175, 175);}#chatgpt-mermaid-\_r\_rg\_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}Buyer natural-languageinstructionIntent Extraction AgentChannel3 Product DiscoveryExact Product SelectionPromise Receipt CompilerBuyer ApprovalPayPal Orders API: AUTHORIZEAuthorization RecordMerchant Fulfillment AdapterPromise Drift EngineAll Conditions Pass?PayPal Capture APIBlock Capture / ReviewCorrect / Void / ReauthorizeVerified PayPal WebhookPromise Replay / Final ReceiptYesNo

### Frontend

React, Vite, TypeScript and Tailwind.

Three primary views:

1.  Shopper Agent: natural-language instruction, product selection and purchase approval.
    
2.  Promise Receipt: immutable purchase constraints, payment authorization and evidence.
    
3.  Merchant Promise Control Tower: drift cases, fulfillment events, authorization status and capture decisions.
    

### Backend

Python FastAPI modular monolith.

Modules:

*   Intent extraction.
    
*   Channel3 product adapter.
    
*   Promise Receipt compiler.
    
*   Deterministic Promise Drift Engine.
    
*   PayPal payment adapter.
    
*   Merchant fulfillment adapter.
    
*   Webhook verification and event processor.
    
*   Audit and decision service.
    

Do not split these into microservices for the hackathon.

### Database

PostgreSQL.

Table

Purpose

purchase\_intents

Original instruction and approved constraints

product\_snapshots

Channel3 product and variant details

merchant\_promises

Seller quote and fulfillment commitment

promise\_receipts

Frozen, versioned contract

paypal\_transactions

Order, authorization, capture and void IDs

fulfillment\_events

Merchant and carrier events

drift\_findings

Detected deviations and supporting evidence

decision\_events

Buyer approval and rule outcomes

webhook\_events

Verified, deduplicated PayPal events

Use append-only financial and decision events. A cryptographic hash can make recorded history tamper-evident; it cannot prove that an externally supplied fulfillment event is truthful.

### Critical security boundaries

*   PayPal client secrets stay server-side.
    
*   LLM receives no PayPal credentials.
    
*   The model cannot create or capture a payment directly.
    
*   Product descriptions and merchant messages are untrusted data.
    
*   Approved buyer constraints cannot be silently rewritten by AI.
    
*   All capture and void operations use idempotency.
    
*   PayPal Developer+1
    

5\. Sponsor tools: meaningful integrations, not sponsor stacking
================================================================

This is an important part of the competition strategy. The hackathon permits multiple sponsor tools, and its FAQ says a submission can compete for the applicable sponsor prize categories, subject to the overall limit on winning prizes.

Devpost+1

I would select five tools, with four having clear workflow purposes.

[How to integrate product data from multiple sources into a single API](https://images.openai.com/static-rsc-4/elypFwqftukCAGxYkOIdH1OMqLYQ75rYW1JUmaiOInzIfU4bcStUeW95yIffHhJv3CJKWgR2hzz4Ln04IdbsLJH4fRA-yrwmjU48i_bO4TCy1ZnF2TSDaa80olUurV6KcV6QZhMzrzKmzitMgieS10eIv1MtmLR7DoKD13QrsZc?purpose=inline)

1\. Channel3

Runtime product integration

Real product discovery, normalized product metadata, variants, pricing and availability. Save the exact API response used to establish the approved purchase snapshot.

Why it matters: the Promise Receipt must preserve the actual selected product identity, not merely an LLM's summary.

[Sponsor resources](https://paypalaihackathon.devpost.com/details/channel3?utm_source=chatgpt.com).

Devpost

[AG Studio: High-Performance React Dashboard, Angular Dashboard, JavaScript Dashboard](https://images.openai.com/static-rsc-4/3O7IQOcJnPd7UJkAEBTVChBaAqV8ddEaVKYuv6PnueNdmN0d7i2gqxKGiVND4TqMM0l4URxnTizKIfZI_sYSv1aIYI4h-CmM4bUtmvTp2N_XbMuVm8zXpBqPDhwaa7g_ynSqu2IizdnMxdzo3JaLgIoEHl708p3OID5WDumGx9I?purpose=inline)

2\. AG Grid AG Studio

Runtime product integration

Build a Promise Control Tower with a customized exception grid, promise-status widgets, cross-filtering and the Studio Agent Framework.

Example read-only question: "Show purchases with product mismatches and authorized payments approaching expiry."

Why it matters: the data becomes an operational decision interface rather than a decorative dashboard.

[Sponsor resources](https://paypalaihackathon.devpost.com/details/aggrid?utm_source=chatgpt.com).

Devpost

[Standard API Definitions Demystified | Nordic APIs |](https://images.openai.com/static-rsc-4/QqbGRs0ubEyetkWb2T2vCqAWowwNm_N1em-wG1p1O70_4GdxqSiXwOHFKhlBT0k_fVKbWmuSwBYoF3THM3ZTUaxz9nC7SHc6rO5H_lNy8eSoQEHfVtd2vsgSg35ZR48tyFm09C440Muve07Uz7YGNGRHh343nA2lm-hLG9Yfzdk?purpose=inline)

3\. APIMatic

Development integration

Use the PayPal Context Plugin through the AI coding environment while implementing Orders, authorizations, capture, void and webhooks.

Document its actual contribution to the implementation.

Why it matters: this is precisely the type of PayPal integration use the APIMatic sponsor is promoting.

[Sponsor resources](https://paypalaihackathon.devpost.com/details/apimatic?utm_source=chatgpt.com).

Devpost

[Интеграция Test IT с Postman | Test IT](https://images.openai.com/static-rsc-4/eDP46jptZbnrWrR7zdRQ_a47ByE88fitRbLlFI16GmDbyWlR_BUfmp8_urnDoPlziz1P5HubgTJ8AkwXok_re-iHHpe2bRuS5D-qxhT1gvg3vdHKrSMSKAxc0tqI4e_a7cf2SDfnAJsNFjtDhuUzm7Klvar4WZl8vTA6NzrdNGA?purpose=inline)

4\. Postman

Development and testing

Build an API collection for authorization, capture, void, webhook verification and negative test paths. Include a reusable Sandbox environment.

Why it matters: makes payment integration reproducible and easier to verify.

[Sponsor resources](https://paypalaihackathon.devpost.com/details/postman?utm_source=chatgpt.com).

Devpost

[Render: $100 Million Series C Extension At $1.5 Billion Valuation Raised For Modern Cloud Platform](https://images.openai.com/static-rsc-4/XQ8Itzkko2ukMle7Uxpew8KfTJDML0AFQIELfD8nzBWnDbB2buV_-AsF1NxFDv08z8p-iC-K-GzCon6hOvM1io703iDnnCW5d-XUwc-1wQc1rJI4dj2LRKYXQ0fbQIER6RcL5ZHsIaa7bzs3Cm8EBYEEKdiNbKqTe6vIudIBfWQ?purpose=inline)

5\. Render

Deployment and operations

Deploy frontend, FastAPI backend, PostgreSQL and the background event processor. Consider Render Workflows for retriable asynchronous promise evaluations if its setup proves straightforward.

Why it matters: a stable, publicly accessible demo and webhook listener.

[Sponsor resources](https://paypalaihackathon.devpost.com/details/render?utm_source=chatgpt.com).

Devpost

Do not add Elastic, KERNEL, Astropods, Bryntum or Zapier merely to increase the number of sponsor logos. Their integration costs are not justified by the initial product.

The most strategically valuable sponsor combinations are Channel3 + AG Grid. They create visible, functional product value. APIMatic and Postman improve integration quality. Render delivers the working deployment.

6\. The final build scope
=========================

P0 — Must ship
--------------

*   Natural-language intent extraction into strict structured constraints.
    
*   Real Channel3 product discovery and product snapshot.
    
*   Promise Receipt creation and buyer approval.
    
*   Real PayPal Sandbox authorization using AUTHORIZE.
    
*   Merchant fulfillment event adapter and simulator.
    
*   Promise Drift Engine with deterministic capture gate.
    
*   Actual PayPal capture and void workflows.
    
*   Verified PayPal webhooks and replayable receipt.
    
*   One working AG Studio control tower.
    

P1 — Only after P0 passes
-------------------------

*   Partial refund after a post-capture problem.
    
*   Authorization-expiry reauthorization flow.
    
*   External carrier/merchant integration adapter.
    
*   Read-only MCP interface for third-party shopping agents.
    
*   Additional fulfillment evidence formats.
    

CUT — Out of scope
------------------

*   Generic customer-support chatbot.
    
*   AI shopping marketplace.
    
*   Autonomous refund agent.
    
*   Blockchain or token-based escrow.
    
*   Multi-agent swarm.
    
*   Multi-merchant production onboarding.
    
*   Full logistics platform or CRM.
    

7\. Acceptance tests that define product quality
------------------------------------------------

The product is not done when the interface looks correct. It is done when the following cases pass:

Test

Expected behavior

Exact product and variant shipped

Capture is allowed under the approved conditions

Wrong product variant

Capture blocked

Refurbished substitution

Capture blocked

Total exceeds authorized buyer limit

Contract rejected before authorization

Merchant changes promised terms

Receipt becomes stale; buyer reapproval required

Carrier event missing

Hold for verification

Shipment ETA violates approved deadline

Capture held; review or void decision

Authorization expires

Capture prohibited; renewal workflow required

Same capture event delivered twice

One financial capture only

PayPal webhook signature invalid

Event rejected

Authorization already voided

No capture attempted

This suite provides a much stronger argument for implementation quality than a demonstration of several different LLM agents.

8\. Execution sequence: October 31 – November 12
================================================

Deadline: November 12, 2026, 12:00 PM Pacific Time = November 13, 2026, 1:30 AM IST. Approximately 12 days remain from the current date.

Dates

Critical deliverable

Exit condition

Oct 31–Nov 2

PayPal authorize/capture/void proof, Channel3 access

One working Sandbox authorization and capture

Nov 3–4

Intent parser, product snapshot, Promise Receipt

Buyer can approve an exact contract

Nov 5–6

Fulfillment simulator and drift engine

A wrong variant reliably blocks capture

Nov 7–8

Corrected evidence and automatic conditional capture

Actual capture succeeds only after the required check

Nov 9–10

AG Studio, tests, security and Render deployment

Full workflow works from a clean session

Nov 11

Demo video, README, license and submission content

All judging materials ready

Nov 12

Final submission validation

Submission completed before the deadline

The first hard checkpoint is November 2. If PayPal authorization and capture do not work by then, the scope must be reduced immediately. Do not compensate by building more AI features.

9\. Final product identity — locked direction
=============================================

PromiseLoop
===========

### Promise-Gated Payments for Agentic Commerce

Final product direction

Problem

AI shopping agents can select and pay for products, but the original buyer instruction, selected product, merchant commitments, PayPal payment and fulfillment evidence can become disconnected.

Solution

PromiseLoop creates a verifiable Intent-to-Outcome Contract for every AI-initiated purchase and uses fulfillment evidence to determine when its PayPal authorization can be captured.

Unique feature

Promise-Gated Capture: a payment cannot be settled merely because an AI agent successfully completed checkout. It must satisfy the buyer-approved purchase conditions and required fulfillment evidence.

Proof

A Promise Receipt that allows anyone with appropriate access to replay the original instruction, commercial terms, payment events, detected deviations and final settlement outcome.

Core users

Operators of AI shopping platforms and merchants accepting AI-agent-initiated orders.

The final 30-second pitch
-------------------------

AI agents are learning to buy things for us. But who verifies that they actually bought what we asked for?

Today, an agent can select a product, complete a PayPal transaction, and leave the buyer with disconnected records of what was requested, promised, purchased and fulfilled.

PromiseLoop changes that.

It converts the buyer's original instruction into a verifiable Promise Receipt, connects it to the selected product and PayPal authorization, and checks fulfillment against the approved conditions.

With PayPal's authorize-and-capture lifecycle, money is captured only when the required purchase conditions are verified. If the order deviates, settlement is blocked.

PromiseLoop makes agentic commerce accountable—not just autonomous.

10\. The final strategic verdict
--------------------------------

The important distinction between the old and new concepts:

Old PromiseLoop

Final PromiseLoop

AI customer-support agent

Agentic commerce accountability layer

Starts after a complaint

Begins before payment

Recommends refunds

Controls conditional settlement

Stores conversation and order information

Creates an Intent-to-Outcome Contract

Competes with helpdesk software

Complements shopping agents, merchant systems and payment infrastructure

Uses PayPal to issue refunds

Uses PayPal authorization, capture and void as core financial state transitions

The winning idea is not "AI can buy products." That has already been demonstrated by multiple entries.

It is not "AI can block dangerous payments." Warden and similar projects have demonstrated that.

It is not "AI can track orders and issue refunds." Existing commerce platforms have demonstrated that.

It is that an AI-initiated purchase should carry its original human-approved commitments all the way to financial settlement, and the settlement should be governed by whether those commitments were fulfilled.

That is the concept to build.

The most important limitation is that an intent receipt and merchant/carrier event do not constitute independent proof of the physical goods inside a package. The first implementation should make its evidence boundaries explicit. Its deeper value is the deterministic relationship between what was approved and what the merchant's systems subsequently report.

My final product decision: keep PromiseLoop, but lock Promise-Gated Settlement + Promise Receipt + Promise Replay as the inseparable product core. Everything else serves those three capabilities or stays out of the MVP.

This is a substantially stronger and more distinctive product thesis than the original AI refund assistant.