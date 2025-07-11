#!/usr/bin/env python3
"""
Test flow recovery with a real existing flow
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

async def test_real_flow_recovery():
    # Use the most recent flow from the database
    REAL_FLOW_ID = "30b0fe17-1f9c-43fc-92d4-c03bc35973e5"
    
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
            
            print(f"🔍 Step 3: Navigate to field mapping for flow {REAL_FLOW_ID}...")
            field_mapping_url = f"http://localhost:8081/discovery/field-mapping?flowId={REAL_FLOW_ID}"
            await page.goto(field_mapping_url)
            await page.wait_for_load_state("networkidle")
            
            # Wait a bit for any async loading
            await page.wait_for_timeout(3000)
            
            # Take screenshot of field mapping page
            await page.screenshot(path="real_field_mapping_page.png")
            print("📸 Screenshot saved: real_field_mapping_page.png")
            
            print("🗂️ Step 4: Look for field mappings and continue buttons...")
            
            # Check for field mappings table/content
            field_mappings_content = await page.locator('[data-testid="field-mappings"], .field-mappings, table').count()
            print(f"Found {field_mappings_content} field mapping containers")
            
            # Look for continue buttons
            continue_buttons = await page.locator('button:has-text("Continue")').count()
            data_cleansing_buttons = await page.locator('button:has-text("Data Cleansing")').count()
            next_buttons = await page.locator('button:has-text("Next")').count()
            
            print(f"Found {continue_buttons} continue buttons")
            print(f"Found {data_cleansing_buttons} data cleansing buttons")
            print(f"Found {next_buttons} next buttons")
            
            # Try to find any buttons with specific text patterns
            all_buttons = await page.locator('button').all()
            print(f"Total buttons found: {len(all_buttons)}")
            
            button_texts = []
            for button in all_buttons:
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        button_texts.append(text.strip())
                except:
                    pass
            
            print(f"Button texts found: {button_texts}")
            
            # Try to find the continue button and click it
            continue_button_found = False
            for button in all_buttons:
                try:
                    text = await button.text_content()
                    if text and ("continue" in text.lower() or "data cleansing" in text.lower() or "next" in text.lower()):
                        print(f"🚀 Step 5: Clicking button with text: '{text}'")
                        await button.click()
                        await page.wait_for_timeout(3000)
                        
                        # Take screenshot after clicking
                        await page.screenshot(path="after_continue_button_click.png")
                        print("📸 Screenshot saved: after_continue_button_click.png")
                        
                        continue_button_found = True
                        break
                except:
                    pass
            
            if not continue_button_found:
                print("⚠️ No continue button found - checking page content...")
                
                # Check for any error messages or status indicators
                error_elements = await page.locator('.error, .alert-error, .text-red-500').count()
                if error_elements > 0:
                    error_text = await page.locator('.error, .alert-error, .text-red-500').first.text_content()
                    print(f"❌ Error found: {error_text}")
                
                # Try to manually trigger the continue action via JavaScript
                print("🔧 Step 6: Attempting manual flow continuation...")
                
                # Check if there's a specific flow handler we can call
                result = await page.evaluate(f"""
                    // Try to find and call any flow continuation methods
                    let result = {{ success: false, message: 'No continuation method found' }};
                    
                    // Check for React components or global functions
                    if (window.continueFlow) {{
                        try {{
                            window.continueFlow('{REAL_FLOW_ID}');
                            result = {{ success: true, message: 'Called window.continueFlow' }};
                        }} catch (e) {{
                            result = {{ success: false, message: 'Error calling continueFlow: ' + e.message }};
                        }}
                    }}
                    
                    // Check for any data-* attributes that might trigger actions
                    const actionElements = document.querySelectorAll('[data-action*="continue"], [data-action*="next"]');
                    if (actionElements.length > 0) {{
                        result.foundActionElements = actionElements.length;
                    }}
                    
                    return result;
                """)
                
                print(f"JavaScript result: {result}")
            
            print("🔍 Step 7: Check final page state...")
            current_url = page.url
            print(f"Final URL: {current_url}")
            
            # Take final screenshot
            await page.screenshot(path="final_real_flow_state.png")
            print("📸 Screenshot saved: final_real_flow_state.png")
            
            print("📋 Step 8: Analysis of API calls...")
            flow_api_calls = [call for call in api_calls if "flows" in call["url"] or REAL_FLOW_ID in call["url"]]
            print(f"Total API calls: {len(api_calls)}")
            print(f"Flow-related API calls: {len(flow_api_calls)}")
            
            for call in flow_api_calls:
                print(f"  {call['method']} {call['url']}")
                
            print("✅ Test completed successfully!")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_real_flow_recovery())