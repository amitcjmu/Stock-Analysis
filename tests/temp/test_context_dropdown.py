#!/usr/bin/env python3
"""
Test context dropdown functionality
"""
import asyncio
from playwright.async_api import async_playwright

async def test_context_dropdown():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in\n")
            
            # Go to discovery page where context selector is visible
            print("📍 Navigating to Discovery Overview...")
            await page.goto("http://localhost:8081/discovery/overview")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Look for client dropdown
            print("🔍 Looking for context selector...")
            
            # Find the select/dropdown that shows "Demo Corporation"
            # Look for the client selector specifically
            client_selectors = [
                'button:has-text("Demo Corporation")',
                'div:has-text("Client") >> button[role="combobox"]',
                '[data-testid="client-selector"]',
                'button[role="combobox"]:has-text("Corporation")'
            ]
            
            client_dropdown = None
            for selector in client_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        client_dropdown = element.first
                        break
                except:
                    continue
                    
            if not client_dropdown:
                # Try to find by looking at all comboboxes
                all_dropdowns = await page.locator('button[role="combobox"]').all()
                for dropdown in all_dropdowns:
                    text = await dropdown.inner_text()
                    if "Corporation" in text or "Client" in text:
                        client_dropdown = dropdown
                        break
                        
            if client_dropdown:
                client_text = await client_dropdown.inner_text()
                print(f"Current client: {client_text}")
                
                # Click to open dropdown
                await client_dropdown.click()
                await page.wait_for_timeout(1000)
            else:
                print("❌ Could not find client dropdown")
                # Take screenshot to see what's on the page
                await page.screenshot(path="page_without_client_dropdown.png")
                print("📸 Screenshot saved: page_without_client_dropdown.png")
                return
            
            # Look for Acme Corporation option
            acme_option = page.locator('div[role="option"]:has-text("Acme Corporation")')
            if await acme_option.count() > 0:
                print("✅ Found Acme Corporation in dropdown")
                await acme_option.click()
                await page.wait_for_timeout(2000)
                
                # Check if engagement dropdown is populated
                print("\n🔍 Checking engagement dropdown...")
                engagement_dropdown = page.locator('button[role="combobox"]').nth(1)
                
                # Wait for engagement dropdown to be available
                await page.wait_for_timeout(1000)
                engagement_text = await engagement_dropdown.inner_text()
                print(f"Engagement dropdown text: {engagement_text}")
                
                # Click engagement dropdown
                await engagement_dropdown.click()
                await page.wait_for_timeout(1000)
                
                # Count engagement options
                engagement_options = await page.locator('div[role="option"]').count()
                print(f"✅ Found {engagement_options} engagement options")
                
                # List all options
                for i in range(engagement_options):
                    option_text = await page.locator('div[role="option"]').nth(i).inner_text()
                    print(f"  - {option_text}")
                
                # Take screenshot
                await page.screenshot(path="context_dropdown_engagements.png")
                print("\n📸 Screenshot saved: context_dropdown_engagements.png")
            else:
                print("❌ Could not find Acme Corporation in dropdown")
                
                # List all available options
                all_options = await page.locator('div[role="option"]').all_inner_texts()
                print(f"Available options: {all_options}")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_context_dropdown())