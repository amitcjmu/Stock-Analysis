import { test, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:8081';
const TEST_USER = {
  email: 'analyst@demo-corp.com',
  password: 'Demo123!'
};

test.describe('Trigger Field Mapping', () => {
  test('Upload file and trigger field mapping', async ({ page }) => {
    test.setTimeout(300000); // 5 minutes

    // Login
    console.log('🔐 Logging in...');
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);

    // Navigate to CMDB Import
    console.log('📁 Navigating to CMDB Import...');
    await page.goto(`${BASE_URL}/discovery/cmdb-import`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Upload file
    console.log('📤 Uploading CMDB file...');

    // Look for upload areas (we know there are 4 from debugging)
    const uploadAreas = await page.locator('.border-dashed, [data-testid="upload-area"], .upload-zone').all();
    console.log(`Found ${uploadAreas.length} upload areas`);

    if (uploadAreas.length === 0) {
      // Try alternative selectors
      const altUploadAreas = await page.locator('div:has(input[type="file"]), [role="button"]:has-text("upload")').all();
      console.log(`Found ${altUploadAreas.length} alternative upload areas`);

      if (altUploadAreas.length > 0) {
        uploadAreas.push(...altUploadAreas);
      }
    }

    if (uploadAreas.length === 0) {
      throw new Error('No upload areas found on CMDB import page');
    }

    // Try clicking the first upload area
    const firstUploadArea = uploadAreas[0];
    console.log('🎯 Clicking first upload area...');
    await firstUploadArea.click();
    await page.waitForTimeout(1000);

    // Look for file input after clicking
    const fileInput = page.locator('input[type="file"]');
    const fileInputCount = await fileInput.count();
    console.log(`File inputs found: ${fileInputCount}`);

    if (fileInputCount === 0) {
      throw new Error('No file input found after clicking upload area');
    }

    // Upload the file
    const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
    console.log('Uploading file:', testFilePath);
    await fileInput.first().setInputFiles(testFilePath);
    await page.waitForTimeout(5000);
    console.log('✅ File uploaded');

    // Wait for initial processing
    console.log('⏳ Waiting for initial processing...');
    await page.waitForTimeout(10000);

    // Navigate to Attribute Mapping
    console.log('🗺️ Navigating to Attribute Mapping...');
    await page.goto(`${BASE_URL}/discovery/attribute-mapping`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take screenshot before triggering
    await page.screenshot({ path: 'test-results/before-trigger-mapping.png', fullPage: true });

    // Check if "Trigger Field Mapping" button exists
    const triggerButton = page.locator('button:has-text("Trigger Field Mapping")');
    if (await triggerButton.isVisible()) {
      console.log('🔄 Clicking "Trigger Field Mapping" button...');
      await triggerButton.click();

      // Wait for processing
      console.log('⏳ Waiting for field mapping to process...');
      await page.waitForTimeout(15000); // Give it 15 seconds

      // Take screenshot after triggering
      await page.screenshot({ path: 'test-results/after-trigger-mapping.png', fullPage: true });

      // Check for mapping data
      const mappingIndicators = [
        'table',
        'thead',
        'tbody',
        'tr:has(td)',
        'text=/source.*field/i',
        'text=/target.*field/i',
        'text=/column/i',
        'text=/attribute/i',
        '.mapping-table',
        '[data-testid*="mapping"]'
      ];

      let foundMapping = false;
      for (const indicator of mappingIndicators) {
        const count = await page.locator(indicator).count();
        if (count > 0) {
          console.log(`✅ Found mapping indicator: ${indicator} (${count} elements)`);
          foundMapping = true;
        }
      }

      if (!foundMapping) {
        console.log('❌ No mapping data found after triggering');

        // Check if still showing "No Field Mapping Available"
        const noMappingMessage = await page.locator('text="No Field Mapping Available"').count();
        if (noMappingMessage > 0) {
          console.log('⚠️ Still showing "No Field Mapping Available" message');
        }
      } else {
        // Look for finalize/save button
        console.log('🎯 Looking for finalize/save button...');
        const actionButtons = [
          'button:has-text("Finalize")',
          'button:has-text("Save")',
          'button:has-text("Apply")',
          'button:has-text("Complete")',
          'button:has-text("Continue")',
          'button:has-text("Next")'
        ];

        for (const buttonSelector of actionButtons) {
          const button = page.locator(buttonSelector).first();
          if (await button.isVisible()) {
            console.log(`🔘 Clicking ${buttonSelector}...`);
            await button.click();
            await page.waitForTimeout(5000);
            break;
          }
        }
      }
    } else {
      console.log('❌ "Trigger Field Mapping" button not found');

      // Check if mapping data already exists
      const existingMapping = await page.locator('table, tbody, tr:has(td)').count();
      if (existingMapping > 0) {
        console.log('✅ Mapping data already exists');
      }
    }

    // Navigate to inventory to check results
    console.log('📋 Navigating to Inventory...');
    await page.goto(`${BASE_URL}/discovery/inventory`);
    await page.waitForTimeout(5000);
    await page.screenshot({ path: 'test-results/inventory-after-mapping.png', fullPage: true });

    // Count assets
    const assetRows = await page.locator('tbody tr, tr:has(td), .asset-row, [data-testid*="asset"]').count();
    console.log(`\n📊 Final Results:`);
    console.log(`- Assets in inventory: ${assetRows}`);

    // Get asset counts from the UI
    const totalAssets = await page.locator('text=/Total.*Assets/i').locator('..').locator('text=/\\d+/').first().textContent();
    const servers = await page.locator('text="Servers"').locator('..').locator('text=/\\d+/').first().textContent();
    const applications = await page.locator('text="Applications"').locator('..').locator('text=/\\d+/').first().textContent();

    console.log(`- Total IT Assets: ${totalAssets || '0'}`);
    console.log(`- Servers: ${servers || '0'}`);
    console.log(`- Applications: ${applications || '0'}`);

    // Assert that assets were created
    expect(parseInt(totalAssets || '0')).toBeGreaterThan(0);
  });
});
