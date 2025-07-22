#!/usr/bin/env python3
"""
Test all main navigation routes
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_all_routes():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track all errors
        all_errors = {}
        
        async def handle_response(response):
            if "/api/" in response.url and response.status >= 400:
                route_name = current_route if 'current_route' in locals() else 'Unknown'
                if route_name not in all_errors:
                    all_errors[route_name] = []
                
                error_info = {
                    "url": response.url,
                    "status": response.status,
                    "endpoint": response.url.split('/api/v1/')[-1] if '/api/v1/' in response.url else response.url
                }
                
                try:
                    data = await response.json()
                    error_info["detail"] = data.get("detail", str(data))
                except:
                    pass
                
                all_errors[route_name].append(error_info)
                print(f"❌ {route_name}: {error_info['endpoint']} - {error_info['status']}")
        
        page.on("response", handle_response)
        
        try:
            # Login first
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in successfully\n")
            
            # Define all routes to test
            routes = [
                ("Discovery Overview", "/discovery/overview"),
                ("CMDB Import", "/discovery/cmdb-import"),  
                ("Attribute Mapping", "/discovery/attribute-mapping"),
                ("Application Portfolio", "/discovery/application-portfolio"),
                ("Dependency Analysis", "/discovery/dependency-analysis"),
                ("6R Analysis", "/sixr-analysis"),
                ("Assessment Readiness", "/discovery/assessment-readiness"),
                ("Client Management", "/admin/clients"),
                ("Engagement Setup", "/admin/engagements"),
                ("User Management", "/admin/users"),
                ("Client Context", "/context/client"),
                ("Engagement Context", "/context/engagement"),
                ("User Profile", "/context/user")
            ]
            
            # Test each route
            for route_name, route_path in routes:
                current_route = route_name
                print(f"\n📍 Testing: {route_name}")
                
                # Clear previous errors for this route
                if route_name in all_errors:
                    all_errors[route_name] = []
                
                await page.goto(f"http://localhost:8081{route_path}")
                await page.wait_for_load_state("networkidle", timeout=5000)
                await page.wait_for_timeout(2000)  # Extra wait for all API calls
                
                if route_name not in all_errors or len(all_errors[route_name]) == 0:
                    print("  ✅ No errors")
                else:
                    print(f"  ❌ {len(all_errors[route_name])} errors found")
            
            # Summary
            print("\n" + "="*60)
            print("SUMMARY OF ERRORS:")
            print("="*60)
            
            total_errors = 0
            for route, errors in all_errors.items():
                if errors:
                    print(f"\n{route}: {len(errors)} errors")
                    for error in errors:
                        print(f"  - {error['endpoint']}: {error['status']}")
                        if 'detail' in error:
                            print(f"    {error['detail']}")
                    total_errors += len(errors)
            
            if total_errors == 0:
                print("\n✅ All routes working without errors!")
            else:
                print(f"\n❌ Total errors found: {total_errors}")
                
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_all_routes())