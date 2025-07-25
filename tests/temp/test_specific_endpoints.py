#!/usr/bin/env python3
"""
Test specific problematic endpoints
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_endpoints():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))

        # Track all requests
        async def handle_request(request):
            if "data-import" in request.url:
                print(f"\n📤 Request: {request.method} {request.url}")
                headers = await request.all_headers()
                if "x-client-account-id" in headers:
                    print(f"   Client ID: {headers['x-client-account-id']}")
                if "x-engagement-id" in headers:
                    print(f"   Engagement ID: {headers['x-engagement-id']}")

        async def handle_response(response):
            if "data-import" in response.url:
                print(f"📥 Response: {response.status} {response.url}")
                if response.status >= 400:
                    try:
                        data = await response.json()
                        print(f"   Error: {json.dumps(data, indent=2)}")
                    except:
                        text = await response.text()
                        print(f"   Text: {text}")

        page.on("request", handle_request)
        page.on("response", handle_response)

        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)

            # Navigate to Attribute Mapping
            print("\n📍 Navigating to Attribute Mapping...")
            await page.goto("http://localhost:8081/discovery/attribute-mapping")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)

            # Try to find the actual URLs being requested
            print("\n🔍 Page loaded. Checking network activity...")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_endpoints())
