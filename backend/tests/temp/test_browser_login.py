#!/usr/bin/env python3
"""
Test login flow using Playwright to simulate real browser behavior
"""
import asyncio

from playwright.async_api import async_playwright


async def test_login():
    async with async_playwright() as p:
        # Launch browser with headless=False to see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Enable console logging
        page = await context.new_page()
        
        # Log console messages
        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        
        # Log network requests
        page.on("request", lambda request: print(f"[REQUEST] {request.method} {request.url}"))
        page.on("response", lambda response: print(f"[RESPONSE] {response.status} {response.url}"))
        
        try:
            print("🌐 Navigating to login page...")
            await page.goto("http://localhost:8081/login", wait_until="networkidle")
            
            print("📝 Filling login form...")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            
            print("🖱️ Clicking Sign In button...")
            await page.click('button:has-text("Sign In")')
            
            # Wait for navigation or error
            print("⏳ Waiting for response...")
            
            # Wait for either success navigation or error message
            try:
                # Wait for successful navigation away from login page
                await page.wait_for_url("http://localhost:8081/", timeout=5000)
                print("✅ Login successful! Redirected to home page")
            except:
                # Check for error messages
                error_element = page.locator('.text-red-500, .text-destructive, [role="alert"]')
                if await error_element.count() > 0:
                    error_text = await error_element.first.text_content()
                    print(f"❌ Login failed with error: {error_text}")
                else:
                    print("❌ Login failed - timeout waiting for redirect")
            
            # Take a screenshot
            await page.screenshot(path="login_result.png")
            print("📸 Screenshot saved as login_result.png")
            
            # Wait a bit to see console logs
            await page.wait_for_timeout(2000)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_login())