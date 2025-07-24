#!/usr/bin/env python3
"""
Simple test to check authentication flow
"""
import asyncio
import json

from playwright.async_api import async_playwright


async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Intercept API responses
        api_responses = []

        async def handle_response(response):
            if "/api/v1/auth/login" in response.url:
                try:
                    data = await response.json()
                    api_responses.append(
                        {"url": response.url, "status": response.status, "data": data}
                    )
                    print("\n📡 Login API Response:")
                    print(f"   Status: {response.status}")
                    print(f"   Data: {json.dumps(data, indent=2)}")
                except Exception:
                    pass

        page.on("response", handle_response)

        # Capture console logs
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            print("🌐 Navigating to login page...")
            await page.goto("http://localhost:8081/login")
            await page.wait_for_load_state("networkidle")

            print("📝 Filling login form...")
            await page.fill('input[type="email"]', "chocka@gmail.com")
            await page.fill('input[type="password"]', "Password123!")

            print("🖱️ Clicking Sign In button...")
            await page.click('button:has-text("Sign In")')

            # Wait for API response
            await page.wait_for_timeout(3000)

            # Check current URL
            current_url = page.url
            print(f"\n📍 Current URL: {current_url}")

            # Check for authentication headers in console
            print("\n📋 Console logs related to auth:")
            for log in console_logs:
                if any(
                    keyword in log.lower()
                    for keyword in ["auth", "user", "header", "token", "login"]
                ):
                    print(f"   {log}")

            # Take screenshot
            await page.screenshot(path="auth_test_result.png")
            print("\n📸 Screenshot saved as auth_test_result.png")

        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_login())
