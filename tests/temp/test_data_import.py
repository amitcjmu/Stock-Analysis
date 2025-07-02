#!/usr/bin/env python3
"""
Test data import functionality
"""
import asyncio
from playwright.async_api import async_playwright
import json

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
            
            # Wait for validation to complete
            print("⏳ Waiting for validation...")
            await page.wait_for_selector('text="Validation completed successfully"', timeout=30000)
            print("✅ Validation completed!")
            
            # Take screenshot after validation
            await page.screenshot(path="data_import_validated.png")
            print("📸 Screenshot saved: data_import_validated.png")
            
            # Clean up test file
            import os
            os.unlink(test_file_path)
            print("\n🧹 Cleaned up test file")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_data_import())