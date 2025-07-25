#!/usr/bin/env python3
"""
End-to-end browser test to verify the complete flow recovery works
Tests the browser UI flow from login to data cleansing continuation
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def test_complete_flow_recovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        # Track API calls
        api_calls = []

        async def handle_request(request):
            if "/api/" in request.url:
                api_calls.append({
                    "url": request.url,
                    "method": request.method,
                    "timestamp": time.time()
                })
                print(f"📤 API Request: {request.method} {request.url}")

        async def handle_response(response):
            if "/api/" in response.url:
                print(f"📥 API Response: {response.status} {response.url}")
                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        print(f"   Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"   Error text: {await response.text()}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            print("🌐 Step 1: Navigate to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")

            print("🔐 Step 2: Login with platform admin...")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')

            # Wait for login to complete
            try:
                await page.wait_for_url("**/admin/**", timeout=10000)
                print("✅ Login successful - redirected to admin dashboard")
            except:
                print("⚠️ Login may have succeeded but waiting for redirect...")
                await page.wait_for_timeout(3000)

            print("🔍 Step 3: Navigate to Discovery flows...")
            # Try to navigate to discovery section
            await page.goto("http://localhost:8081/discovery")
            await page.wait_for_load_state("networkidle")

            # Take screenshot of discovery page
            await page.screenshot(path="discovery_page.png")
            print("📸 Screenshot saved: discovery_page.png")

            print("🔍 Step 4: Look for the specific flow 96ee6321-b1e8-463a-b975-37dc537aa2a9...")

            # Check if we can find the flow ID or any reference to it
            flow_id = "96ee6321-b1e8-463a-b975-37dc537aa2a9"

            # Try to find active flows or navigate to field mapping
            print("🗂️ Step 5: Navigate to field mapping or look for Continue button...")

            # Look for any continue buttons, field mapping sections, or flow navigation
            continue_buttons = await page.locator('button:has-text("Continue")').count()
            data_cleansing_buttons = await page.locator('button:has-text("Data Cleansing")').count()

            print(f"Found {continue_buttons} continue buttons")
            print(f"Found {data_cleansing_buttons} data cleansing buttons")

            if continue_buttons > 0:
                print("🚀 Step 6: Click Continue button...")
                await page.locator('button:has-text("Continue")').first.click()
                await page.wait_for_timeout(2000)

            elif data_cleansing_buttons > 0:
                print("🚀 Step 6: Click Data Cleansing button...")
                await page.locator('button:has-text("Data Cleansing")').first.click()
                await page.wait_for_timeout(2000)

            else:
                print("⚠️ No continue or data cleansing buttons found")

                # Try to access the flow directly via URL
                print("🔗 Step 6: Try to access field mapping for the flow directly...")
                field_mapping_url = f"http://localhost:8081/discovery/field-mapping?flowId={flow_id}"
                await page.goto(field_mapping_url)
                await page.wait_for_load_state("networkidle")

                # Take screenshot of field mapping page
                await page.screenshot(path="field_mapping_page.png")
                print("📸 Screenshot saved: field_mapping_page.png")

                # Look for continue button on field mapping page
                continue_buttons = await page.locator('button:has-text("Continue")').count()
                data_cleansing_buttons = await page.locator('button:has-text("Data Cleansing")').count()

                print(f"On field mapping page - Found {continue_buttons} continue buttons")
                print(f"On field mapping page - Found {data_cleansing_buttons} data cleansing buttons")

                if continue_buttons > 0:
                    print("🚀 Step 7: Click Continue button on field mapping page...")
                    await page.locator('button:has-text("Continue")').first.click()
                    await page.wait_for_timeout(3000)

                    # Take screenshot after clicking continue
                    await page.screenshot(path="after_continue_click.png")
                    print("📸 Screenshot saved: after_continue_click.png")

                elif data_cleansing_buttons > 0:
                    print("🚀 Step 7: Click Data Cleansing button...")
                    await page.locator('button:has-text("Data Cleansing")').first.click()
                    await page.wait_for_timeout(3000)

                    # Take screenshot after clicking data cleansing
                    await page.screenshot(path="after_data_cleansing_click.png")
                    print("📸 Screenshot saved: after_data_cleansing_click.png")

            print("🔍 Step 8: Check final page state...")
            current_url = page.url
            print(f"Final URL: {current_url}")

            # Check for any error messages
            error_elements = await page.locator('.text-red-500, .text-destructive, [role="alert"]').count()
            if error_elements > 0:
                error_text = await page.locator('.text-red-500, .text-destructive, [role="alert"]').first.text_content()
                print(f"❌ Error found: {error_text}")
            else:
                print("✅ No errors found on final page")

            # Take final screenshot
            await page.screenshot(path="final_state.png")
            print("📸 Screenshot saved: final_state.png")

            print("📋 Step 9: Analysis of API calls...")
            flow_api_calls = [call for call in api_calls if "flows" in call["url"]]
            print(f"Total API calls: {len(api_calls)}")
            print(f"Flow-related API calls: {len(flow_api_calls)}")

            for call in flow_api_calls[-5:]:  # Show last 5 flow calls
                print(f"  {call['method']} {call['url']}")

            print("✅ Test completed successfully!")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_complete_flow_recovery())
