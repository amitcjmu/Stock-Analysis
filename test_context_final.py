#!/usr/bin/env python3
"""
Test context switching in header
"""
import asyncio
from playwright.async_api import async_playwright

async def test_context_switching():
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
            
            # Navigate to discovery page directly
            print("📍 Navigating to Discovery page...")
            await page.goto("http://localhost:8081/discovery/overview")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Look for the context display in the header
            print("🔍 Looking for context in header...")
            
            # Take screenshot to see current state
            await page.screenshot(path="discovery_page_state.png")
            print("📸 Screenshot saved: discovery_page_state.png")
            
            # Look for Demo Corporation text in header
            demo_corp_elements = await page.locator('text="Demo Corporation"').count()
            print(f"Found {demo_corp_elements} 'Demo Corporation' elements")
            
            # Look for Switch Context button/element
            switch_context_button = page.locator('button:has-text("Switch Context")')
            if await switch_context_button.count() > 0:
                print("✅ Found 'Switch Context' button")
                
                # Click the Switch Context button
                print("\n🔄 Clicking Switch Context button...")
                await switch_context_button.click()
                await page.wait_for_timeout(2000)
                
                # Now look for client dropdown in the opened panel
                print("🔍 Looking for client selector in opened panel...")
                
                # Try to find select/combobox elements in the popup
                selects_in_popup = await page.locator('div[role="dialog"] button[role="combobox"], div[data-radix-popper-content-wrapper] button[role="combobox"]').count()
                print(f"Found {selects_in_popup} select elements in popup")
                
                if selects_in_popup > 0:
                    # Click the first combobox (should be client selector)
                    client_selector = page.locator('div[role="dialog"] button[role="combobox"], div[data-radix-popper-content-wrapper] button[role="combobox"]').first
                    await client_selector.click()
                    await page.wait_for_timeout(1000)
                    
                    # Look for Acme Corporation
                    acme_option = page.locator('div[role="option"]:has-text("Acme Corporation")')
                    if await acme_option.count() > 0:
                        print("✅ Found Acme Corporation, selecting it...")
                        await acme_option.click()
                        await page.wait_for_timeout(2000)
                        
                        # Now check engagement dropdown
                        print("\n🔍 Checking engagement dropdown...")
                        engagement_selector = page.locator('div[role="dialog"] button[role="combobox"], div[data-radix-popper-content-wrapper] button[role="combobox"]').nth(1)
                        await engagement_selector.click()
                        await page.wait_for_timeout(1000)
                        
                        # Count engagement options
                        engagement_options = await page.locator('div[role="option"]').count()
                        print(f"✅ Found {engagement_options} engagement options")
                        
                        # List engagements
                        for i in range(min(engagement_options, 5)):  # List first 5
                            option_text = await page.locator('div[role="option"]').nth(i).inner_text()
                            print(f"  - {option_text}")
                            
                        # Take screenshot
                        await page.screenshot(path="context_with_engagements.png")
                        print("\n📸 Screenshot saved: context_with_engagements.png")
                        
                        # Select first engagement
                        if engagement_options > 0:
                            await page.locator('div[role="option"]').first.click()
                            await page.wait_for_timeout(1000)
                            
                            # Apply changes if there's an Apply button
                            apply_button = page.locator('button:has-text("Apply")')
                            if await apply_button.count() > 0:
                                print("\n✅ Applying context changes...")
                                await apply_button.click()
                                await page.wait_for_timeout(2000)
                                print("✅ Context switch completed!")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_context_switching())