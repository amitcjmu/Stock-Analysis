#!/usr/bin/env python3
"""
Complete end-to-end test using demo user account
Goes through: Login -> Continue existing flow -> Field Mapping -> Continue to Data Cleansing
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import re

async def test_complete_demo_flow():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        # Track API calls
        api_calls = []
        flow_id = None

        async def handle_request(request):
            if "/api/" in request.url:
                api_calls.append({
                    "url": request.url,
                    "method": request.method,
                    "timestamp": time.time()
                })
                print(f"📤 API Request: {request.method} {request.url}")

        async def handle_response(response):
            nonlocal flow_id
            if "/api/" in response.url:
                print(f"📥 API Response: {response.status} {response.url}")
                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        print(f"   Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"   Error text: {await response.text()}")
                elif response.status == 200 and "data-import" in response.url:
                    try:
                        # Try to extract flow ID from successful data import
                        response_data = await response.json()
                        if isinstance(response_data, dict) and "flow_id" in response_data:
                            flow_id = response_data["flow_id"]
                            print(f"✅ Extracted flow ID: {flow_id}")
                    except:
                        pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            print("🌐 Step 1: Navigate to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")

            print("🔐 Step 2: Login with demo user account...")
            await page.fill('input[type="email"]', 'demo@demo-corp.com')
            await page.fill('input[type="password"]', 'Demo123!')
            await page.click('button:has-text("Sign In")')

            # Wait for login to complete
            try:
                await page.wait_for_url("**/dashboard", timeout=10000)
                print("✅ Login successful - redirected to dashboard")
            except:
                print("⚠️ Login may have succeeded but waiting for redirect...")
                await page.wait_for_timeout(3000)

            # Take screenshot after login
            await page.screenshot(path="demo_after_login.png")
            print("📸 Screenshot saved: demo_after_login.png")

            print("🗂️ Step 3: Navigate to Discovery section...")
            # Click on the Discovery in the sidebar
            discovery_sidebar = await page.locator('a:has-text("Discovery"), [href*="discovery"]').count()
            if discovery_sidebar > 0:
                await page.locator('a:has-text("Discovery"), [href*="discovery"]').first.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            else:
                # Try navigating directly to CMDB import
                await page.goto("http://localhost:8081/discovery/cmdb-import")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)

            # Take screenshot of discovery page
            await page.screenshot(path="demo_discovery_page.png")
            print("📸 Screenshot saved: demo_discovery_page.png")

            print("📁 Step 4: Navigate to Data Import...")
            # Click on Data Import in the sidebar
            data_import_link = await page.locator('a:has-text("Data Import"), [href*="data-import"]').count()
            if data_import_link > 0:
                await page.locator('a:has-text("Data Import"), [href*="data-import"]').first.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            else:
                # Try navigating directly to CMDB import
                await page.goto("http://localhost:8081/discovery/cmdb-import")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)

            # Take screenshot of data import page
            await page.screenshot(path="demo_data_import_page.png")
            print("📸 Screenshot saved: demo_data_import_page.png")

            print("📁 Step 5: Check for existing flows and navigate to flow details...")

            # Look for flow management buttons
            manage_flows_buttons = await page.locator('button:has-text("Manage Flows")').count()
            view_details_buttons = await page.locator('button:has-text("View Details")').count()

            print(f"Found {manage_flows_buttons} Manage Flows buttons")
            print(f"Found {view_details_buttons} View Details buttons")

            if manage_flows_buttons > 0:
                print("🚀 Step 6: Clicking Manage Flows button...")
                await page.locator('button:has-text("Manage Flows")').first.click()
                await page.wait_for_timeout(3000)

                # Take screenshot after clicking manage flows
                await page.screenshot(path="demo_after_manage_flows.png")
                print("📸 Screenshot saved: demo_after_manage_flows.png")

                # Wait for navigation
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)

            elif view_details_buttons > 0:
                print("🚀 Step 6: Clicking View Details button...")
                await page.locator('button:has-text("View Details")').first.click()
                await page.wait_for_timeout(3000)

                # Take screenshot after clicking view details
                await page.screenshot(path="demo_after_view_details.png")
                print("📸 Screenshot saved: demo_after_view_details.png")

                # Wait for navigation
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)

            else:
                print("⚠️ No Manage Flows or View Details buttons found")

                # Try to extract flow ID from the page and navigate directly
                page_content = await page.content()
                flow_id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page_content)
                if flow_id_match:
                    flow_id = flow_id_match.group(1)
                    print(f"🔗 Extracted flow ID: {flow_id}")

                    # Navigate directly to field mapping for this flow
                    field_mapping_url = f"http://localhost:8081/discovery/field-mapping?flowId={flow_id}"
                    print(f"🔗 Navigating to field mapping: {field_mapping_url}")
                    await page.goto(field_mapping_url)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(3000)

            # Take screenshot of current page (could be flow details or field mapping)
            await page.screenshot(path="demo_flow_page.png")
            print("📸 Screenshot saved: demo_flow_page.png")

            print("🗂️ Step 7: Check field mappings and look for continue button...")

            # Look for continue buttons on field mapping page
            continue_buttons = await page.locator('button:has-text("Continue")').count()
            data_cleansing_buttons = await page.locator('button:has-text("Data Cleansing")').count()
            next_buttons = await page.locator('button:has-text("Next")').count()

            print(f"Found {continue_buttons} continue buttons")
            print(f"Found {data_cleansing_buttons} data cleansing buttons")
            print(f"Found {next_buttons} next buttons")

            # Find all buttons and their text
            all_buttons = await page.locator('button').all()
            button_texts = []
            for button in all_buttons:
                try:
                    text = await button.text_content()
                    if text and text.strip():
                        button_texts.append(text.strip())
                except:
                    pass

            print(f"All button texts: {button_texts}")

            # Try to click the continue button
            continue_clicked = False
            for button in all_buttons:
                try:
                    text = await button.text_content()
                    if text and ("continue" in text.lower() or "data cleansing" in text.lower() or "next" in text.lower()):
                        print(f"🚀 Step 8: Clicking button: '{text}'")
                        await button.click()
                        await page.wait_for_timeout(3000)

                        # Take screenshot after clicking continue
                        await page.screenshot(path="demo_after_continue.png")
                        print("📸 Screenshot saved: demo_after_continue.png")

                        continue_clicked = True
                        break
                except Exception as e:
                    print(f"Error clicking button: {e}")
                    continue

            if not continue_clicked:
                print("⚠️ No continue button found - checking for alternative actions...")

                # Try to manually trigger flow continuation
                print("🔧 Attempting manual flow continuation...")

                # Extract flow ID from the page
                page_content = await page.content()
                flow_id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page_content)
                if flow_id_match:
                    flow_id = flow_id_match.group(1)
                    print(f"🔗 Extracted flow ID: {flow_id}")

                    # Make API call to continue flow
                    result = await page.evaluate(f"""
                        fetch('/api/v1/flows/{flow_id}/execute', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + localStorage.getItem('auth_token')
                                }},
                                body: JSON.stringify({{
                                    phase: 'data_cleansing',
                                    phase_input: {{ test_mode: true }}
                                }})
                            }})
                            .then(response => response.json())
                            .then(data => {{ return {{ success: true, data: data }}; }})
                            .catch(error => {{ return {{ success: false, error: error.message }}; }});
                        """)

                    print(f"API call result: {result}")

                    if result.get("success"):
                        print("✅ Flow continuation successful via API")

                        # Wait and take screenshot
                        await page.wait_for_timeout(3000)
                        await page.screenshot(path="demo_after_api_continue.png")
                        print("📸 Screenshot saved: demo_after_api_continue.png")
                    else:
                        print(f"❌ Flow continuation failed: {result.get('error', 'Unknown error')}")
                else:
                    print("⚠️ Could not extract flow ID from page")

            else:
                print("❌ No Continue Flow button found")

                # Check if there are any error messages
                error_messages = await page.locator('.error, .alert, .warning').count()
                if error_messages > 0:
                    error_text = await page.locator('.error, .alert, .warning').first.text_content()
                    print(f"⚠️ Error message found: {error_text}")

            print("🔍 Step 9: Check final state...")
            current_url = page.url
            print(f"Final URL: {current_url}")

            # Check for any error messages
            error_elements = await page.locator('.error, .alert-error, .text-red-500').count()
            if error_elements > 0:
                error_text = await page.locator('.error, .alert-error, .text-red-500').first.text_content()
                print(f"❌ Error found: {error_text}")
            else:
                print("✅ No errors found")

            # Take final screenshot
            await page.screenshot(path="demo_final_state.png")
            print("📸 Screenshot saved: demo_final_state.png")

            print("📋 Step 10: Analysis of API calls...")
            flow_api_calls = [call for call in api_calls if "flows" in call["url"] or "data-import" in call["url"]]
            print(f"Total API calls: {len(api_calls)}")
            print(f"Flow-related API calls: {len(flow_api_calls)}")

            for call in flow_api_calls:
                print(f"  {call['method']} {call['url']}")

            if flow_id:
                print(f"✅ Flow ID captured: {flow_id}")
            else:
                print("⚠️ No flow ID captured")

            print("✅ Complete demo flow test completed!")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_complete_demo_flow())
