#!/usr/bin/env python3
"""
Simple test to access an existing flow and test the recovery mechanism
"""

import asyncio
from playwright.async_api import async_playwright
import re

async def test_simple_flow_recovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🌐 Step 1: Navigate to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")
            
            print("🔐 Step 2: Login with demo user account...")
            await page.fill('input[type="email"]', 'demo@demo-corp.com')
            await page.fill('input[type="password"]', 'Demo123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_timeout(3000)
            
            print("🗂️ Step 3: Navigate to Discovery Data Import...")
            await page.goto("http://localhost:8081/discovery")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)
            
            # Navigate to Data Import - try direct URL first
            try:
                await page.click('a:has-text("Data Import")', timeout=5000)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            except:
                print("⚠️ Could not find Data Import link, trying direct navigation...")
                await page.goto("http://localhost:8081/discovery/cmdb-import")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
            
            # Take screenshot
            await page.screenshot(path="flow_recovery_data_import.png")
            print("📸 Screenshot saved: flow_recovery_data_import.png")
            
            print("📋 Step 4: Check for existing flows...")
            # Look for manage flows button
            manage_flows_buttons = await page.locator('button:has-text("Manage Flows")').count()
            print(f"Found {manage_flows_buttons} Manage Flows buttons")
            
            if manage_flows_buttons > 0:
                print("🚀 Step 5: Click Manage Flows...")
                await page.click('button:has-text("Manage Flows")')
                await page.wait_for_timeout(2000)
                
                # Take screenshot
                await page.screenshot(path="flow_recovery_manage_flows.png")
                print("📸 Screenshot saved: flow_recovery_manage_flows.png")
                
            # Extract flow ID from page
            page_content = await page.content()
            flow_id_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page_content)
            if flow_id_match:
                flow_id = flow_id_match.group(1)
                print(f"✅ Found flow ID: {flow_id}")
                
                print("🔗 Step 6: Navigate to field mapping...")
                field_mapping_url = f"http://localhost:8081/discovery/field-mapping?flowId={flow_id}"
                await page.goto(field_mapping_url)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
                
                # Take screenshot
                await page.screenshot(path="flow_recovery_field_mapping.png")
                print("📸 Screenshot saved: flow_recovery_field_mapping.png")
                
                print("🔍 Step 7: Look for Continue button...")
                continue_buttons = await page.locator('button:has-text("Continue")').count()
                print(f"Found {continue_buttons} Continue buttons")
                
                if continue_buttons > 0:
                    print("🚀 Step 8: Click Continue button...")
                    await page.click('button:has-text("Continue")')
                    await page.wait_for_timeout(3000)
                    
                    # Take screenshot
                    await page.screenshot(path="flow_recovery_after_continue.png")
                    print("📸 Screenshot saved: flow_recovery_after_continue.png")
                    
                else:
                    print("⚠️ No Continue button found - trying API call...")
                    
                    # Try API call to continue flow
                    result = await page.evaluate(f"""
                        fetch('/api/v1/flows/{flow_id}/execute', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + localStorage.getItem('auth_token'),
                                'X-Client-Account-Id': '21990f3a-abb6-4862-be06-cb6f854e167b',
                                'X-Engagement-Id': '58467010-6a72-44e8-ba37-cc0238724455'
                            }},
                            body: JSON.stringify({{
                                phase_input: {{ test_mode: true }}
                            }})
                        }})
                        .then(response => {{
                            console.log('Response status:', response.status);
                            return response.json().then(data => {{
                                return {{ success: response.ok, status: response.status, data: data }};
                            }});
                        }})
                        .catch(error => {{ 
                            console.error('API call error:', error);
                            return {{ success: false, error: error.message }}; 
                        }});
                    """)
                    
                    print(f"API call result: {result}")
                    
                    if result.get("success"):
                        print("✅ Flow continuation successful via API!")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Data: {result.get('data')}")
                        
                        # Take screenshot
                        await page.screenshot(path="flow_recovery_api_success.png")
                        print("📸 Screenshot saved: flow_recovery_api_success.png")
                        
                        # Now try to navigate to data cleansing to verify flow works
                        print("🔍 Step 8: Testing if flow can now proceed to data cleansing...")
                        data_cleansing_url = f"http://localhost:8081/discovery/data-cleansing?flowId={flow_id}"
                        await page.goto(data_cleansing_url)
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(3000)
                        
                        # Take screenshot
                        await page.screenshot(path="flow_recovery_data_cleansing.png")
                        print("📸 Screenshot saved: flow_recovery_data_cleansing.png")
                        
                    else:
                        print(f"❌ Flow continuation failed: {result.get('error', 'Unknown error')}")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Data: {result.get('data')}")
                        
                        # Take screenshot of failure
                        await page.screenshot(path="flow_recovery_api_failure.png")
                        print("📸 Screenshot saved: flow_recovery_api_failure.png")
                        
            else:
                print("⚠️ No flow ID found on page")
                
            print("✅ Test completed!")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_flow_recovery())