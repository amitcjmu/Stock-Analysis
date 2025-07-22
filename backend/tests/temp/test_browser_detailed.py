#!/usr/bin/env python3
"""
Detailed browser test with request interception
"""
import asyncio
import json

from playwright.async_api import async_playwright


async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track all API requests
        api_requests = []
        
        async def handle_request(request):
            if "/api/v1/auth/login" in request.url:
                headers = await request.all_headers()
                post_data = request.post_data
                api_requests.append({
                    "url": request.url,
                    "method": request.method,
                    "headers": headers,
                    "data": post_data
                })
                print("\n📤 Login Request:")
                print(f"   URL: {request.url}")
                print(f"   Method: {request.method}")
                print(f"   Headers: {json.dumps(headers, indent=4)}")
                if post_data:
                    print(f"   Data: {post_data}")
        
        page.on("request", handle_request)
        
        # Intercept responses
        async def handle_response(response):
            if "/api/v1/auth/login" in response.url:
                try:
                    data = await response.json()
                    print("\n📥 Login Response:")
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {response.headers}")
                    print(f"   Data: {json.dumps(data, indent=2)}")
                except Exception:
                    text = await response.text()
                    print("\n📥 Login Response (text):")
                    print(f"   Status: {response.status}")
                    print(f"   Text: {text}")
        
        page.on("response", handle_response)
        
        try:
            print("🌐 Navigating to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot before login
            await page.screenshot(path="before_login.png")
            
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
            
            # Wait for response
            await page.wait_for_timeout(5000)
            
            # Take screenshot after login attempt
            await page.screenshot(path="after_login.png")
            
            # Check current URL
            current_url = page.url
            print(f"\n📍 Final URL: {current_url}")
            
            # Check for error messages
            error_element = page.locator('.text-red-500, .text-destructive, [role="alert"]')
            if await error_element.count() > 0:
                error_text = await error_element.first.text_content()
                print(f"\n❌ Error displayed: {error_text}")
            
            print("\n✅ Test completed")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())