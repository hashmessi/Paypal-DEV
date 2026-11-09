from playwright.sync_api import sync_playwright
import time

def test_shop():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        target_url = "https://promiseloop-web.onrender.com/shop"
        page.goto(target_url, timeout=45000)
        print("Opened /shop")

        # Step 1 -> Input instruction with $400 budget
        instruction_input = page.locator("#instruction-text")
        instruction_input.fill("Find new black wireless headphones, over-ear, under $400, delivered by Friday. No refurbished.")
        print("Filled instruction with $400 budget")

        # Step 1 -> Extract constraints
        extract_btn = page.locator("button:has-text('Extract constraints')").first
        extract_btn.click()
        page.wait_for_selector("text=Step 2", timeout=15000)
        print("Step 2 visible!")

        # Step 2 -> Search products
        search_btn = page.locator("button:has-text('Search products')").first
        search_btn.click()
        page.wait_for_selector("text=Step 3", timeout=15000)
        print("Step 3 visible!")

        # Step 3 -> Select first candidate offer
        time.sleep(1)
        offer_btn = page.locator("button:has-text('Select offer')").first
        if not offer_btn.is_visible():
            page.locator("h3").first.click()
            time.sleep(0.5)
            offer_btn = page.locator("button:has-text('Select offer')").first
        print("Offer button visible:", offer_btn.is_visible())
        offer_btn.click()
        page.wait_for_selector("text=Step 4", timeout=15000)
        print("Step 4 visible!")

        # Step 4 -> Compile Promise Receipt
        compile_btn = page.locator("button:has-text('Compile Promise Receipt')").first
        compile_btn.click()
        page.wait_for_selector("text=Step 5", timeout=15000)
        print("Step 5 visible!")

        # Step 5 -> Approve receipt
        approve_btn = page.locator("button:has-text('Approve receipt')").first
        approve_btn.click()
        page.wait_for_selector("text=Step 6", timeout=15000)
        print("Step 6 visible!")

        time.sleep(2)
        # Check PayPal button
        paypal_real = page.locator(".paypal-buttons, iframe[title*='PayPal']").first
        paypal_btn = page.locator("button:has-text('Authorize hold'), button:has-text('PayPal')").first
        print("PayPal Real SDK visible:", paypal_real.is_visible())
        print("PayPal Authorize Button visible:", paypal_btn.is_visible())

        # Click authorize button
        if paypal_btn.is_visible():
            paypal_btn.click()
            time.sleep(2)
            open_receipt_btn = page.locator("button:has-text('Open promise receipt')").first
            print("Open promise receipt visible:", open_receipt_btn.is_visible())
            if open_receipt_btn.is_visible():
                open_receipt_btn.click()
                page.wait_for_url("**/receipts/**", timeout=10000)
                print("Navigated to receipt:", page.url)

        browser.close()
        print("Shop flow complete!")

if __name__ == "__main__":
    test_shop()
