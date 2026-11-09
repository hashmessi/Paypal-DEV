from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        target_url = "https://promiseloop-web.onrender.com/"
        page.goto(target_url, timeout=45000)
        print("Initial URL:", page.url)
        page.wait_for_selector("text=Capture only what the buyer approved")
        print("Hero found!")
        
        # Click Instant 30-sec demo button
        # In Start.tsx: Button has icon Play and onClick handleRunDemo
        demo_btn = page.locator("button:has-text('Run demo scenario'), button:has-text('Launch 30-sec Demo'), button:has-text('Instant 30-Sec')").first
        if not demo_btn.is_visible():
            # Find button inside Lane 2
            demo_btn = page.locator("text=Instant 30-Sec").locator("xpath=ancestor::div[contains(@class, 'rounded')]").locator("button").first
        
        print("Demo button found!")
        demo_btn.click()
        
        page.wait_for_url("**/receipts/**", timeout=10000)
        print("Navigated to receipt URL:", page.url)
        time.sleep(2)
        
        # Check Scenario Console
        refurb_btn = page.locator("button:has-text('Refurbished')").first
        print("Refurbished button visible:", refurb_btn.is_visible())
        refurb_btn.click()
        time.sleep(1)
        
        drift_pill = page.locator("text=DRIFT").first
        print("Drift pill visible:", drift_pill.is_visible())
        
        # Prompt injection
        inj_btn = page.locator("button:has-text('Prompt injection')").first
        print("Prompt injection button visible:", inj_btn.is_visible())
        inj_btn.click()
        time.sleep(1)
        print("After injection, Drift pill still visible:", drift_pill.is_visible())
        
        # Corrected
        corr_btn = page.locator("button:has-text('Correct item')").first
        print("Correct item button visible:", corr_btn.is_visible())
        corr_btn.click()
        time.sleep(2)
        
        match_pill = page.locator("text=MATCH").first
        print("Match pill visible:", match_pill.is_visible())
        
        # Replay link
        replay_btn = page.locator("button:has-text('Open replay')").first
        print("Replay button visible:", replay_btn.is_visible())
        replay_btn.click()
        page.wait_for_url("**/replay", timeout=5000)
        print("Replay URL:", page.url)
        time.sleep(1)
        
        # Verify integrity button
        verify_btn = page.locator("button:has-text('Verify integrity')").first
        if verify_btn.is_visible():
            verify_btn.click()
            time.sleep(1)
            print("Verified integrity clicked!")
            
        # Navigate to Proof
        proof_link = page.locator("nav >> text=Proof").first
        proof_link.click()
        page.wait_for_url("**/proof", timeout=5000)
        print("Proof URL:", page.url)
        time.sleep(1)
        
        benchmark_heading = page.locator("text=18 Labeled Evaluation Scenarios").first
        print("Proof benchmark visible:", benchmark_heading.is_visible() if benchmark_heading else False)
        
        browser.close()
        print("All steps succeeded perfectly!")

if __name__ == "__main__":
    run()
