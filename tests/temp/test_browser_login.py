#!/usr/bin/env python3
"""
Browser test to verify login functionality
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()

        # Track all API requests
        api_requests = []

        async def handle_request(request):
            if "/api/" in request.url:
                headers = await request.all_headers()
                post_data = request.post_data
                api_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "headers": headers,
                    "data": post_data
                })
                print("\n📤 API Request:")
                print(f"   URL: {request.url}")
                print(f"   Method: {request.method}")
                if "authorization" in headers:
                    print(f"   Auth: {headers.get('authorization', 'None')[:50]}...")
                if post_data:
                    print(f"   Data: {post_data}")

        page.on("request", handle_request)

        # Intercept responses
        async def handle_response(response):
            if "/api/" in response.url:
                print("\n📥 API Response:")
                print(f"   URL: {response.url}")
                print(f"   Status: {response.status}")
                if response.status >= 400:
                    try:
                        data = await response.json()
                        print(f"   Error: {json.dumps(data, indent=2)}")
                    except:
                        text = await response.text()
                        print(f"   Text: {text}")

        page.on("response", handle_response)

        try:
            print("🌐 Navigating to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")

            # Take screenshot before login
            await page.screenshot(path="before_login.png")
            print("📸 Screenshot saved: before_login.png")

            print("\n📝 Filling login form...")
            email_input = page.locator('input[type="email"]')
            password_input = page.locator('input[type="password"]')

            await email_input.fill('chocka@gmail.com')
            await password_input.fill('Password123!')

            # Verify values are filled
            email_value = await email_input.input_value()
            password_value = await password_input.input_value()
            print(f"   Email: {email_value}")
            print(f"   Password: {'*' * len(password_value)}")

            print("\n🖱️ Clicking Sign In button...")
            await page.click('button:has-text("Sign In")')

            # Wait for response or navigation
            try:
                await page.wait_for_url("**/dashboard", timeout=5000)
                print("\n✅ Successfully logged in! Redirected to dashboard")
            except:
                print("\n⏳ Waiting for response...")
                await page.wait_for_timeout(3000)

            # Take screenshot after login attempt
            await page.screenshot(path="after_login.png")
            print("📸 Screenshot saved: after_login.png")

            # Check current URL
            current_url = page.url
            print(f"\n📍 Final URL: {current_url}")

            # Check for error messages
            error_element = page.locator('.text-red-500, .text-destructive, [role="alert"]')
            if await error_element.count() > 0:
                error_text = await error_element.first.text_content()
                print(f"\n❌ Error displayed: {error_text}")
            else:
                # Check if we're on dashboard
                if "/dashboard" in current_url:
                    print("\n✅ Login successful!")
                else:
                    print("\n⚠️ Login may have succeeded but no redirect occurred")

            print("\n✅ Test completed")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())
