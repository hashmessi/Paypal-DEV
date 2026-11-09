"""
PromiseLoop Automated Live Demo Driver (Calibrated for 3:45 Broadcast Recording)
Provides generous speaking time (12s to 20s per concept) for articulate, clear workflow explanation.
Features a live on-screen Teleprompter HUD with a real-time countdown clock and progress bar.
Target: https://promiseloop-web.onrender.com/
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

DEFAULT_URL = "https://promiseloop-web.onrender.com/"
SHOW_PROMPTER = "--no-prompter" not in sys.argv

CURSOR_HELPER_JS = """
(function() {
    if (document.getElementById('demo-cursor-pointer')) return;
    const cursor = document.createElement('div');
    cursor.id = 'demo-cursor-pointer';
    cursor.style.position = 'fixed';
    cursor.style.width = '24px';
    cursor.style.height = '24px';
    cursor.style.borderRadius = '50%';
    cursor.style.backgroundColor = 'rgba(0, 112, 186, 0.75)';
    cursor.style.border = '2px solid white';
    cursor.style.boxShadow = '0 0 14px rgba(0, 112, 186, 0.9)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '9999998';
    cursor.style.transition = 'transform 0.15s ease-out, background-color 0.2s';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.top = '0px';
    cursor.style.left = '0px';
    document.body.appendChild(cursor);

    window.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });

    window.addEventListener('mousedown', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(0.65)';
        cursor.style.backgroundColor = 'rgba(239, 68, 68, 0.95)';
    });

    window.addEventListener('mouseup', () => {
        cursor.style.transform = 'translate(-50%, -50%) scale(1)';
        cursor.style.backgroundColor = 'rgba(0, 112, 186, 0.75)';
    });
})();
"""

def log_act_cue(page: Page, act_label: str, title: str, spoken_text: str, duration_sec: float):
    """Prints broadcast spoken cues to the console instead of an on-screen overlay."""
    print("\n" + "-" * 65)
    print(f"🎙️  {act_label} · {title} [{duration_sec:.0f}s speaking time]")
    print(f'   "{spoken_text}"')
    print("-" * 65)

def bring_chrome_to_top():
    """Forces Chrome to topmost foreground window on Windows desktop."""
    try:
        import win32gui, win32con
        hwnds = []
        def enum_cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Chrome" in title or "PromiseLoop" in title:
                    hwnds.append(hwnd)
        win32gui.EnumWindows(enum_cb, None)
        for h in hwnds:
            win32gui.ShowWindow(h, win32con.SW_MAXIMIZE)
            win32gui.SetWindowPos(h, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
            win32gui.SetWindowPos(h, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)
    except Exception as e:
        print("[Focus] Note:", e)

def smooth_move(page: Page, target_x: float, target_y: float, steps: int = 25):
    """Smooth human-like mouse movement for recording."""
    page.mouse.move(target_x, target_y, steps=steps)
    time.sleep(0.1)

def highlight_and_click(page: Page, locator, delay_after: float = 2.0):
    """Centers element in viewport, moves mouse to locator, clicks, and pauses for viewer comprehension."""
    try:
        locator.evaluate("el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })")
    except Exception:
        locator.scroll_into_view_if_needed()
    time.sleep(0.6)
    box = locator.bounding_box()
    if box:
        smooth_move(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=25)
        time.sleep(0.4)
        page.mouse.down()
        time.sleep(0.15)
        page.mouse.up()
        time.sleep(delay_after)
    else:
        locator.click()
        time.sleep(delay_after)

def inject_helpers(page: Page):
    page.evaluate(CURSOR_HELPER_JS)

def run_demo(target_url: str = DEFAULT_URL, headed: bool = True):
    print("=" * 68)
    print("PROMISELOOP BROADCAST LIVE DEMO DRIVER (PACED FOR 3:45 RECORDING)")
    print("=" * 68)
    print(f"Mode: {'Headed Chrome (Visible Desktop)' if headed else 'Headless'}")
    print("Screen Overlay: 100% CLEAN (Zero dark cards / banners)")
    print(f"Target URL: {target_url}\n")

    with sync_playwright() as p:
        launch_args = {
            "channel": "chrome",
            "headless": not headed,
            "args": [
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        }
        
        browser = p.chromium.launch(**launch_args)
        # Use no_viewport=True so Chrome uses the full, native maximized screen without letterbox bars or DPI scaling distortion
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        # ------------------------------------------------------------------
        # ACT 1: OPENING HOOK (0:00 - 0:15 | 15s)
        # ------------------------------------------------------------------
        print("[ACT 1] Opening Hook & Hero Headline...")
        page.goto(target_url, timeout=45000)
        inject_helpers(page)
        bring_chrome_to_top()
        page.wait_for_selector("text=Capture only what the buyer approved")
        
        act1_duration = 14.0
        log_act_cue(
            page,
            "Act 1 / 10",
            "Opening Hook",
            "Autonomous AI agents are starting to spend human money. But right now, when an agent buys the wrong item, payment gateways auto-capture the funds immediately.",
            act1_duration
        )
        time.sleep(act1_duration)

        # ------------------------------------------------------------------
        # ACT 2: THE PROBLEM & STAKES (0:15 - 0:35 | 20s)
        # ------------------------------------------------------------------
        print("[ACT 2] Highlighting the $3.75 Dispute Multiplier...")
        act2_duration = 18.0
        log_act_cue(
            page,
            "Act 2 / 10",
            "The Problem & Stakes",
            "Merchants lose $3.75 for every dollar disputed. What the buyer authorized, what the seller promised, and what the carrier delivers live in separate silos.",
            act2_duration
        )
        problem_box = page.locator("text=The $3.75 Dispute Multiplier").first
        box = problem_box.bounding_box()
        if box:
            smooth_move(page, box["x"] + 130, box["y"] + 30, steps=30)
        time.sleep(act2_duration)

        # ------------------------------------------------------------------
        # ACT 3: PRODUCT & SANDBOX LANE (0:35 - 0:55 | 20s)
        # ------------------------------------------------------------------
        print("[ACT 3] Introducing PromiseLoop & Launching Real Sandbox Lane...")
        act3_duration = 18.0
        log_act_cue(
            page,
            "Act 3 / 10",
            "Product Architecture",
            "Meet PromiseLoop. We invert settlement: money is held under PayPal Orders v2 authorization. Capture happens only when physical fulfillment matches the frozen promise.",
            act3_duration
        )
        launch_sandbox_btn = page.locator("button:has-text('Launch Real Sandbox Flow')").first
        box = launch_sandbox_btn.bounding_box()
        if box:
            smooth_move(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=25)
        time.sleep(7.0)

        highlight_and_click(page, launch_sandbox_btn, delay_after=2.0)
        page.wait_for_url("**/shop", timeout=15000)
        inject_helpers(page)
        bring_chrome_to_top()
        time.sleep(act3_duration - 9.0)

        # ------------------------------------------------------------------
        # ACT 4A: STEP 1 - NATURAL LANGUAGE INTENT (0:55 - 1:15 | 20s)
        # ------------------------------------------------------------------
        print("[ACT 4A] Step 1: Inputting Instruction...")
        act4a_duration = 18.0
        log_act_cue(
            page,
            "Act 4 / 10",
            "Step 1: Buyer Instruction",
            "Watch this live. A shopper gives a natural language request. Gemini extracts strict purchase constraints into typed schemas.",
            act4a_duration
        )
        instruction_text = "Find new black wireless headphones, over-ear, under $400, delivered by Friday. No refurbished."
        textarea = page.locator("#instruction-text")
        textarea.fill("")
        textarea.type(instruction_text, delay=22)
        time.sleep(5.0)

        extract_btn = page.locator("button:has-text('Extract constraints')").first
        highlight_and_click(page, extract_btn, delay_after=2.0)
        page.wait_for_selector("text=Step 2", timeout=15000)
        time.sleep(act4a_duration - 12.0)

        # ------------------------------------------------------------------
        # ACT 4B: STEP 2 - FROZEN CONSTRAINTS (1:15 - 1:30 | 15s)
        # ------------------------------------------------------------------
        print("[ACT 4B] Step 2: Reviewing Frozen Constraints...")
        act4b_duration = 15.0
        log_act_cue(
            page,
            "Act 4 / 10",
            "Step 2: Frozen Constraints",
            "Notice how the constraints are frozen: condition NEW, max budget $400. Relative delivery dates are resolved deterministically by the server clock, not the AI.",
            act4b_duration
        )
        search_btn = page.locator("button:has-text('Search products')").first
        box = search_btn.bounding_box()
        if box:
            smooth_move(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=20)
        time.sleep(9.0)

        highlight_and_click(page, search_btn, delay_after=2.0)
        page.wait_for_selector("text=Step 3", timeout=15000)
        time.sleep(4.0)

        # ------------------------------------------------------------------
        # ACT 4C: STEP 3 - DISCOVERED CANDIDATES (1:30 - 1:45 | 15s)
        # ------------------------------------------------------------------
        print("[ACT 4C] Step 3: Selecting Catalog Candidate...")
        act4c_duration = 14.0
        log_act_cue(
            page,
            "Act 4 / 10",
            "Step 3: Real Catalog Candidate",
            "Channel3 discovers matching catalog candidates. The buyer selects the exact product and variant.",
            act4c_duration
        )
        offer_btn = page.locator("button:has-text('Select offer')").first
        if not offer_btn.is_visible():
            page.locator("h3").first.click()
            time.sleep(0.5)
            offer_btn = page.locator("button:has-text('Select offer')").first
        time.sleep(6.0)

        highlight_and_click(page, offer_btn, delay_after=2.0)
        page.wait_for_selector("text=Step 4", timeout=15000)
        time.sleep(6.0)

        # ------------------------------------------------------------------
        # ACT 4D: STEP 4 & 5 - QUOTE & RFC 8785 RECEIPT (1:45 - 2:05 | 20s)
        # ------------------------------------------------------------------
        print("[ACT 4D] Step 4 & 5: Merchant Quote & Cryptographic Receipt...")
        act4d_duration = 18.0
        log_act_cue(
            page,
            "Act 4 / 10",
            "Step 4 & 5: RFC 8785 Sealed Receipt",
            "The merchant checkout total is confirmed independently. All terms are compiled into an RFC 8785 canonical JSON receipt, cryptographically sealed with SHA-256.",
            act4d_duration
        )
        compile_receipt_btn = page.locator("button:has-text('Compile Promise Receipt')").first
        highlight_and_click(page, compile_receipt_btn, delay_after=2.0)
        page.wait_for_selector("text=Step 5", timeout=15000)
        time.sleep(6.0)

        approve_receipt_btn = page.locator("button:has-text('Approve receipt')").first
        highlight_and_click(page, approve_receipt_btn, delay_after=2.0)
        page.wait_for_selector("text=Step 6", timeout=15000)
        time.sleep(8.0)

        # ------------------------------------------------------------------
        # ACT 4E: STEP 6 - PAYPAL ORDERS V2 AUTHORIZATION HOLD (2:05 - 2:30 | 25s)
        # ------------------------------------------------------------------
        print("[ACT 4E] Step 6: PayPal Authorization Hold & Custom ID Anchor...")
        act4e_duration = 24.0
        log_act_cue(
            page,
            "Act 4 / 10",
            "Step 6: PayPal Authorization Hold",
            "We authorize—never auto-capture—via PayPal Orders v2, anchoring the receipt hash directly into PayPal's custom_id. Funds are reserved, but zero money moves.",
            act4e_duration
        )
        paypal_btn = page.locator("button:has-text('Authorize hold'), button:has-text('PayPal')").first
        highlight_and_click(page, paypal_btn, delay_after=3.5)

        open_receipt_btn = page.locator("button:has-text('Open promise receipt')").first
        page.wait_for_selector("button:has-text('Open promise receipt')", timeout=15000)
        time.sleep(6.0)  # Pause on green authorization box
        highlight_and_click(page, open_receipt_btn, delay_after=2.0)
        page.wait_for_url("**/receipts/**", timeout=15000)
        inject_helpers(page)
        bring_chrome_to_top()

        # Dwell on Truth Panel
        truth_panel = page.locator("text=PayPal Transaction Engine").first
        if truth_panel.is_visible():
            box = truth_panel.bounding_box()
            if box:
                smooth_move(page, box["x"] + 150, box["y"] + 50, steps=25)
        time.sleep(12.0)

        # ------------------------------------------------------------------
        # ACT 5: THE WOW MOMENT - DRIFT DETECTED (2:30 - 2:50 | 20s)
        # ------------------------------------------------------------------
        print("\n[ACT 5] Invariant Drift Triggered (INV-01 Condition Mismatch)...")
        act5a_duration = 18.0
        log_act_cue(
            page,
            "Act 5 / 10",
            "The Wow Moment: Drift Detected",
            "Now the seller ships a refurbished unit. The drift engine ingests carrier telemetry, flags INV-01, and instantly locks PayPal capture.",
            act5a_duration
        )
        refurb_btn = page.locator("button:has-text('Refurbished item')").first
        highlight_and_click(page, refurb_btn, delay_after=2.0)
        
        # Hover over the red Finding Banner
        banner = page.locator("text=INV-01").first
        if banner.is_visible():
            box = banner.bounding_box()
            if box:
                smooth_move(page, box["x"] + 100, box["y"] + 20, steps=20)
        time.sleep(act5a_duration - 4.0)

        # ------------------------------------------------------------------
        # ACT 5B: ADVERSARIAL PROMPT INJECTION DEFENSE (2:50 - 3:10 | 20s)
        # ------------------------------------------------------------------
        print("Simulating Adversarial Prompt Injection in Carrier Note...")
        act5b_duration = 18.0
        log_act_cue(
            page,
            "Act 5 / 10",
            "Adversarial Prompt Injection Attack",
            "What if the seller injects prompt injection into the carrier notes? Our deterministic gate ignores LLM confusion. Pure invariant code controls money. Escrow remains safe.",
            act5b_duration
        )
        inj_btn = page.locator("button:has-text('Prompt injection attack')").first
        highlight_and_click(page, inj_btn, delay_after=2.0)
        time.sleep(act5b_duration - 4.0)

        # ------------------------------------------------------------------
        # ACT 6: CORRECTION, LIVE MATCH & CAPTURE (3:10 - 3:30 | 20s)
        # ------------------------------------------------------------------
        print("\n[ACT 6] Seller sends Corrected Stock + Carrier Scan...")
        act6_duration = 18.0
        log_act_cue(
            page,
            "Act 6 / 10",
            "Correction & Settlement Capture",
            "Once the seller ships brand-new stock and UPS verifies acceptance, the gate unlocks. PayPal captures the authorized funds and pushes tracking to Orders v2.",
            act6_duration
        )
        corr_btn = page.locator("button:has-text('Correct item')").first
        highlight_and_click(page, corr_btn, delay_after=2.5)

        match_banner = page.locator("text=Fulfillment verified against all frozen constraints").first
        if match_banner.is_visible():
            match_banner.scroll_into_view_if_needed()
            box = match_banner.bounding_box()
            if box:
                smooth_move(page, box["x"] + 150, box["y"] + 20, steps=20)
        time.sleep(act6_duration - 5.0)

        # ------------------------------------------------------------------
        # ACT 7 & 8: REPLAY AUDIT & AP2 ALIGNMENT (3:30 - 3:55 | 25s)
        # ------------------------------------------------------------------
        print("\n[ACT 7 & 8] Opening Replay Audit Timeline...")
        act7_duration = 22.0
        log_act_cue(
            page,
            "Act 7 & 8 / 10",
            "Cryptographic Replay & AP2 Mandate",
            "Every state transition is stored on an append-only, SHA-256 hash-chained ledger. Promise Replay gives full forensic auditability, exportable as a Google AP2 mandate.",
            act7_duration
        )
        replay_btn = page.locator("button:has-text('Open replay')").first
        highlight_and_click(page, replay_btn, delay_after=2.0)
        page.wait_for_url("**/replay", timeout=6000)
        inject_helpers(page)
        time.sleep(4.0)

        verify_btn = page.locator("button:has-text('Verify integrity')").first
        if verify_btn.is_visible():
            highlight_and_click(page, verify_btn, delay_after=2.0)
        time.sleep(act7_duration - 8.0)

        # ------------------------------------------------------------------
        # ACT 9 & 10: PROOF BENCHMARK & CLOSE (3:55 - 4:20 | 25s)
        # ------------------------------------------------------------------
        print("\n[ACT 9 & 10] Navigating to Proof Benchmark Dashboard...")
        act9_duration = 24.0
        log_act_cue(
            page,
            "Act 9 & 10 / 10",
            "Proof Dashboard & Close",
            "Our Proof Dashboard proves 100% unsafe captures prevented across 18 benchmark scenarios, avoiding over $5,200 in dispute losses. The LLM interprets intent. Deterministic code controls money. That's PromiseLoop.",
            act9_duration
        )
        proof_nav = page.locator("nav >> text=Proof").first
        highlight_and_click(page, proof_nav, delay_after=2.0)
        page.wait_for_url("**/proof", timeout=6000)
        inject_helpers(page)
        time.sleep(6.0)

        # Slow, graceful scroll across the benchmark metrics
        page.mouse.wheel(0, 320)
        time.sleep(act9_duration - 8.0)

        print("\n" + "=" * 68)
        print("REAL SANDBOX LIVE DEMO WALKTHROUGH COMPLETED SUCCESSFULLY")
        print("=" * 68)
        time.sleep(3.0)

        context.close()
        browser.close()

if __name__ == "__main__":
    is_headless = "--headless" in sys.argv
    url_arg = next((arg for arg in sys.argv[1:] if arg.startswith("http")), DEFAULT_URL)
    run_demo(target_url=url_arg, headed=not is_headless)
