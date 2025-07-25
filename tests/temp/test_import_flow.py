#!/usr/bin/env python3
"""
Test data import flow without waiting for validation
"""
import asyncio
from playwright.async_api import async_playwright

async def test_data_import():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()

        # Track console logs
        page.on("console", lambda msg: print(f"Console: {msg.text}"))

        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("http://localhost:8081/login")
            await page.fill('input[type="email"]', 'chocka@gmail.com')
            await page.fill('input[type="password"]', 'Password123!')
            await page.click('button:has-text("Sign In")')
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("✅ Logged in\n")

            # Navigate to data import page
            print("📍 Navigating to Data Import page...")
            await page.goto("http://localhost:8081/discovery/import")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(3000)

            # Take screenshot
            await page.screenshot(path="data_import_page.png")
            print("📸 Screenshot saved: data_import_page.png")

            # Create a test CSV file
            import tempfile
            import csv

            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                csv_writer = csv.writer(f)
                csv_writer.writerow(['CI_NAME', 'CI_TYPE', 'STATUS'])
                csv_writer.writerow(['WEB-SERVER-01', 'Server', 'Active'])
                csv_writer.writerow(['DB-SERVER-01', 'Database', 'Active'])
                csv_writer.writerow(['APP-SERVER-01', 'Application', 'Active'])
                test_file_path = f.name

            print(f"\n📄 Created test CSV file: {test_file_path}")

            # Click on CMDB Export Data
            print("\n🖱️ Selecting CMDB Export Data...")
            await page.click('text="CMDB Export Data"')
            await page.wait_for_timeout(1000)

            # Upload the file
            print("📤 Uploading test file...")
            file_input = page.locator('input#file-cmdb')  # Specific to CMDB upload
            await file_input.set_input_files(test_file_path)
            await page.wait_for_timeout(2000)

            # Wait for response message
            print("⏳ Waiting for upload response...")
            await page.wait_for_timeout(5000)

            # Take screenshot after upload
            await page.screenshot(path="data_import_after_upload.png")
            print("📸 Screenshot saved: data_import_after_upload.png")

            # Clean up test file
            import os
            os.unlink(test_file_path)
            print("\n🧹 Cleaned up test file")

            # Check backend logs
            print("\n📋 Checking backend logs...")
            import subprocess
            result = subprocess.run(['docker-compose', 'logs', 'backend', '--tail', '20'],
                                    capture_output=True, text=True)
            print("\nBackend logs (last 20 lines):")
            print(result.stdout)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_data_import())
