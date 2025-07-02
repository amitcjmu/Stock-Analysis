#!/usr/bin/env python3
"""
Test Admin Dashboard to verify platform admins can see all clients
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_admin_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track errors
        errors = []
        
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
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
                print(f"❌ API Error: {response.url} - {response.status}")
        
        page.on("response", handle_response)
        
        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in\n")
            
            # Navigate to Admin Dashboard
            print("📍 Navigating to Admin Dashboard...")
            await page.goto("http://localhost:8081/admin/clients")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Check for client count
            print("🔍 Checking for clients...")
            
            # Look for client cards or list items
            client_elements = await page.locator('[data-testid="client-card"], .client-item, tr[data-client-id]').count()
            
            if client_elements == 0:
                # Try other selectors
                client_elements = await page.locator('tbody tr').count()
                
            print(f"✅ Found {client_elements} client(s) in the dashboard")
            
            # Check for specific text indicating multiple clients
            page_text = await page.locator('body').inner_text()
            
            if "Complete Test Client" in page_text:
                print("✅ Found 'Complete Test Client'")
            if "Acme Corporation" in page_text:
                print("✅ Found 'Acme Corporation'")
            if "TechCorp Industries" in page_text:
                print("✅ Found 'TechCorp Industries'")
            if "Global Enterprises" in page_text:
                print("✅ Found 'Global Enterprises'")
                
            # Take screenshot
            await page.screenshot(path="admin_dashboard_clients.png")
            print("📸 Screenshot saved: admin_dashboard_clients.png")
            
            # Navigate to Engagements
            print("\n📍 Navigating to Engagements...")
            await page.goto("http://localhost:8081/admin/engagements")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)
            
            # Check for engagement count
            engagement_elements = await page.locator('[data-testid="engagement-card"], .engagement-item, tr[data-engagement-id]').count()
            
            if engagement_elements == 0:
                # Try other selectors
                engagement_elements = await page.locator('tbody tr').count()
                
            print(f"✅ Found {engagement_elements} engagement(s) in the dashboard")
            
            # Take screenshot
            await page.screenshot(path="admin_dashboard_engagements.png")
            print("📸 Screenshot saved: admin_dashboard_engagements.png")
            
            if errors:
                print(f"\n❌ Found {len(errors)} API errors:")
                for error in errors:
                    print(f"  - {error['url']}: {error['status']}")
                    if 'detail' in error:
                        print(f"    {error['detail']}")
                        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_admin_dashboard())