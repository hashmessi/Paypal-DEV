# Quick 261102-mmv: Apply design-audit P0+P1 frontend fixes

Executed inline by the orchestrator (no subagents, no commits — user requested no commit).

## P0
1. api.ts: clear cold-start timer; only flag waking if fetch still pending
2. Receipt.tsx: state-dependent "authorized, not captured" callout
3. Receipt.tsx: "Capture status" row -> "Capture ID"
4. Tower.tsx grid: vertically centered cell renderers, fit-width flex columns, autoHeight
5. Sidebar.tsx: Drift queue vs Control tower active state

## P1
- Type scale 12/14/18/28 only (11->12, 13->14, 15/16/20 mapped)
- Sentence-case titles matching sidebar labels
- Two page widths (wide 1280 / narrow 768 centered): Start, Spine
- Badge: one casing/size rule; Synthetic = neutral outlined
- Refs nowrap; clickable div rows -> Link/button; neutral zero KPIs; drop topbar avatar; Events table scroll

## Verify
tsc / oxlint / vite build in frontend
