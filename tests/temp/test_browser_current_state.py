#!/usr/bin/env python3
"""
Check current browser state after fixes
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_current_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track API errors
        api_errors = []
        
        async def handle_response(response):
            if "/api/" in response.url and response.status >= 400:
                print("\n❌ API Error:")
                print(f"   URL: {response.url}")
                print(f"   Status: {response.status}")
                try:
                    data = await response.json()
                    print(f"   Error: {json.dumps(data, indent=2)}")
                    api_errors.append({
                        "url": response.url,
                        "status": response.status,
                        "error": data
                    })
                except:
                    pass
        
        page.on("response", handle_response)
        
        try:
            print("🌐 Navigating to dashboard...")
            # Go directly to dashboard if already logged in
            await page.goto("http://localhost:8081/admin/dashboard")
            await page.wait_for_load_state("networkidle")
            
            # Check if we're redirected to login
            if "/login" in page.url:
                print("📝 Need to login first...")
                email_input = page.locator('input[type="email"]')
                password_input = page.locator('input[type="password"]')
                
                await email_input.fill('chocka@gmail.com')
                await password_input.fill('Password123!')
                await page.click('button:has-text("Sign In")')
                
                await page.wait_for_url("**/dashboard", timeout=5000)
            
            print(f"\n📍 Current URL: {page.url}")
            
            # Wait a bit for all API calls to complete
            await page.wait_for_timeout(3000)
            
            # Take screenshot
            await page.screenshot(path="dashboard_current_state.png")
            print("📸 Screenshot saved: dashboard_current_state.png")
            
            # Summary of errors
            if api_errors:
                print(f"\n⚠️ Found {len(api_errors)} API errors:")
                for error in api_errors:
                    print(f"   - {error['url'].split('/')[-1]}: {error['status']}")
            else:
                print("\n✅ No API errors found!")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_current_state())