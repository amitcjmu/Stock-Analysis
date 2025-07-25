#!/usr/bin/env python3
"""
Test context switching functionality
"""
import asyncio
from playwright.async_api import async_playwright

async def test_context_switching():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()

        # Track errors

        page.on("console", lambda msg: print(f"Console: {msg.text}") if "error" in msg.text.lower() else None)

        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in\n")

            # Wait for context selector to load
            await page.wait_for_timeout(2000)

            # Click on the Switch Context button
            print("🔄 Opening context switcher...")
            await page.click('button:has-text("Switch Context")')
            await page.wait_for_timeout(1000)

            # Take screenshot of context switcher
            await page.screenshot(path="context_switcher_open.png")
            print("📸 Screenshot saved: context_switcher_open.png")

            # Select Acme Corporation
            print("\n🏢 Selecting Acme Corporation...")
            await page.click('button[role="combobox"]:has-text("Demo Corporation")')
            await page.wait_for_timeout(500)
            await page.click('div[role="option"]:has-text("Acme Corporation")')
            await page.wait_for_timeout(1000)

            # Check if engagements dropdown is populated
            print("🔍 Checking engagements dropdown...")
            engagement_dropdown = page.locator('button[role="combobox"]').nth(1)
            engagement_text = await engagement_dropdown.inner_text()
            print(f"Engagement dropdown shows: {engagement_text}")

            # Click on engagement dropdown
            await engagement_dropdown.click()
            await page.wait_for_timeout(500)

            # Count available engagements
            engagement_options = await page.locator('div[role="option"]').count()
            print(f"✅ Found {engagement_options} engagement options")

            # Select first engagement
            if engagement_options > 0:
                await page.locator('div[role="option"]').first.click()
                await page.wait_for_timeout(500)

                # Apply the context switch
                print("\n✅ Applying context switch...")
                await page.click('button:has-text("Apply Context")')
                await page.wait_for_timeout(2000)

                # Verify context switched
                current_context = await page.locator('text="Acme Corporation"').count()
                if current_context > 0:
                    print("✅ Context successfully switched to Acme Corporation!")
                else:
                    print("❌ Context switch may have failed")

            # Take final screenshot
            await page.screenshot(path="context_switched.png")
            print("📸 Screenshot saved: context_switched.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_context_switching())
