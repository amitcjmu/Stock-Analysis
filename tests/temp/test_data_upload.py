#!/usr/bin/env python3
"""
Test Data Upload page specifically
"""
import asyncio
from playwright.async_api import async_playwright

async def test_data_upload():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track errors
        errors = []
        
        page.on("console", lambda msg: print(f"Console: {msg.text}") if "error" in msg.text.lower() else None)
        
        async def handle_response(response):
            if response.status >= 400:
                error_info = {
                    "url": response.url,
                    "status": response.status
                }
                try:
                    data = await response.json()
                    error_info["detail"] = data.get("detail", str(data))
                except:
                    pass
                errors.append(error_info)
                print(f"❌ API Error: {response.url.split('/')[-1]} - {response.status}")
        
        page.on("response", handle_response)
        
        # Handle uncaught exceptions
        page.on("pageerror", lambda error: print(f"❌ Page Error: {error}"))
        
        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in\n")
            
            # Navigate to Data Upload (Discovery Import)
            print("📍 Navigating to Data Upload (Discovery Import)...")
            await page.goto("http://localhost:8081/discovery/import")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Check if page loaded without errors
            if not errors:
                print("✅ Data Upload page loaded successfully!")
                
                # Take screenshot
                await page.screenshot(path="data_upload_page.png")
                print("📸 Screenshot saved: data_upload_page.png")
                
                # Check for upload area or any upload-related elements
                upload_elements = [
                    'text="Drop your CSV or Excel file here"',
                    'text="Upload"',
                    'input[type="file"]',
                    'text="Import"',
                    'text="CMDB"'
                ]
                
                found_element = False
                for selector in upload_elements:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        print(f"✅ Found element: {selector}")
                        found_element = True
                        break
                
                if not found_element:
                    print("⚠️ No upload-related elements found")
                    # List visible text on the page
                    visible_text = await page.locator('body').inner_text()
                    print(f"\nVisible text preview (first 500 chars):\n{visible_text[:500]}...")
                    
            else:
                print(f"\n❌ Found {len(errors)} errors:")
                for error in errors:
                    print(f"  - {error['url']}: {error['status']}")
                    if 'detail' in error:
                        print(f"    {error['detail']}")
                        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_data_upload())