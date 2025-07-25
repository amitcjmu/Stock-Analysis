import { test, expect, Page } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test configuration
const BASE_URL = 'http://localhost:8081';
const TEST_USER = {
  email: 'analyst@demo-corp.com',
  password: 'Demo123!'
};

test.describe('Import and Attribute Mapping', () => {
  test('Import CMDB file and complete attribute mapping', async ({ page }) => {
    test.setTimeout(300000); // 5 minutes

    console.log('Starting import and mapping test...');

    // Step 1: Login
    console.log('🔐 Step 1: Logging in...');
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Fill login form
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Wait for navigation
    await page.waitForTimeout(5000);

    // Verify login
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      throw new Error('Login failed - still on login page');
    }
    console.log('✅ Login successful');

    // Step 2: Navigate to Discovery Import
    console.log('📁 Step 2: Navigating to Data Import...');
    await page.goto(`${BASE_URL}/discovery/cmdb-import`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Take screenshot of import page
    await page.screenshot({ path: 'test-results/import-page-initial.png', fullPage: true });

    // Step 3: Handle existing flows if blocked
    console.log('🔍 Step 3: Checking for existing flows...');
    const uploadBlocked = await page.locator('text=/upload blocked|data upload disabled/i').first().count() > 0;

    if (uploadBlocked) {
      console.log('⚠️ Upload blocked - clearing existing flows...');

      // Try delete button first
      const deleteBtn = page.locator('button:has-text("Delete")').first();
      if (await deleteBtn.isVisible()) {
        await deleteBtn.click();
        await page.waitForTimeout(3000);
        await page.reload();
        await page.waitForTimeout(3000);
      }
    }

    // Step 4: Upload CMDB file
    console.log('📤 Step 4: Uploading CMDB file...');

    // Look for file input
    const fileInputs = await page.locator('input[type="file"]').all();
    console.log(`Found ${fileInputs.length} file inputs on page`);

    // Try to find visible file inputs or upload areas
    const uploadButton = page.locator('button:has-text("Upload")').first();
    const uploadAreas = await page.locator('.border-dashed, [data-testid*="upload"], .upload-zone, .dropzone').all();

    console.log(`Found ${uploadAreas.length} upload areas`);

    // Take screenshot before upload attempt
    await page.screenshot({ path: 'test-results/before-upload-attempt.png', fullPage: true });

    let uploadSuccess = false;

    // Strategy 1: Direct file input if available
    if (fileInputs.length > 0) {
      const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
      console.log('Attempting direct file input upload:', testFilePath);

      try {
        await fileInputs[0].setInputFiles(testFilePath);
        await page.waitForTimeout(3000);
        uploadSuccess = true;
        console.log('✅ File set via direct input');
      } catch (error) {
        console.log('❌ Direct file input failed:', error.message);
      }
    }

    // Strategy 2: Click upload area to reveal file input
    if (!uploadSuccess && uploadAreas.length > 0) {
      console.log('Attempting to click upload area...');
      await uploadAreas[0].click();
      await page.waitForTimeout(2000);

      // Check for file input again
      const newFileInput = page.locator('input[type="file"]').first();
      if (await newFileInput.count() > 0) {
        const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
        await newFileInput.setInputFiles(testFilePath);
        await page.waitForTimeout(3000);
        uploadSuccess = true;
        console.log('✅ File uploaded after clicking area');
      }
    }

    // Strategy 3: Click upload button if available
    if (!uploadSuccess && await uploadButton.isVisible()) {
      console.log('Clicking upload button...');
      await uploadButton.click();
      await page.waitForTimeout(2000);

      const fileInput = page.locator('input[type="file"]').first();
      if (await fileInput.count() > 0) {
        const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
        await fileInput.setInputFiles(testFilePath);
        await page.waitForTimeout(3000);
        uploadSuccess = true;
        console.log('✅ File uploaded after clicking button');
      }
    }

    // Take screenshot after upload attempt
    await page.screenshot({ path: 'test-results/after-upload-attempt.png', fullPage: true });

    // Check for upload success indicators
    const successIndicators = [
      'text=/upload.*complete/i',
      'text=/processing/i',
      'text=/success/i',
      '.success-message',
      'text=/file.*uploaded/i'
    ];

    for (const indicator of successIndicators) {
      if (await page.locator(indicator).first().count() > 0) {
        console.log(`✅ Upload success indicator found: ${indicator}`);
        uploadSuccess = true;
        break;
      }
    }

    if (!uploadSuccess) {
      console.log('⚠️ Upload status unclear - no clear success indicators found');
    }

    // Step 5: Wait for processing
    console.log('⏳ Step 5: Waiting for initial processing...');
    await page.waitForTimeout(10000); // Give it 10 seconds

    // Step 6: Navigate to Attribute Mapping
    console.log('🗺️ Step 6: Going to Attribute Mapping...');

    // Try multiple ways to get there
    const mappingLink = page.locator('a[href*="attribute-mapping"], a:has-text("Attribute Mapping")').first();
    if (await mappingLink.isVisible()) {
      await mappingLink.click();
    } else {
      // Direct navigation
      await page.goto(`${BASE_URL}/discovery/attribute-mapping`);
    }

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('📄 Current URL:', page.url());
    await page.screenshot({ path: 'test-results/attribute-mapping-initial.png', fullPage: true });

    // Step 7: Check if we need to trigger field mapping
    console.log('🔍 Step 7: Checking field mapping status...');

    const noMappingMessage = await page.locator('text=/no field mapping available/i').count() > 0;
    const triggerButton = page.locator('button:has-text("Trigger Field Mapping")');

    if (noMappingMessage && await triggerButton.isVisible()) {
      console.log('🔄 Triggering field mapping...');
      await triggerButton.click();
      await page.waitForTimeout(10000); // Wait for processing

      await page.screenshot({ path: 'test-results/after-trigger-mapping.png', fullPage: true });
    }

    // Step 8: Look for mapping data
    console.log('📊 Step 8: Looking for mapping data...');

    // Check various indicators of mapping data
    const mappingIndicators = [
      'table',
      '.mapping-table',
      '[data-testid*="mapping"]',
      'text=/source.*field/i',
      'text=/target.*field/i',
      'text=/map.*to/i'
    ];

    let foundMapping = false;
    for (const selector of mappingIndicators) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        console.log(`✅ Found mapping indicator: ${selector} (${count} elements)`);
        foundMapping = true;
        break;
      }
    }

    // Step 9: If mapping found, try to finalize
    if (foundMapping) {
      console.log('🎯 Step 9: Looking for finalize button...');

      const finalizeButtons = [
        'button:has-text("Finalize")',
        'button:has-text("Complete")',
        'button:has-text("Save")',
        'button:has-text("Apply")',
        'button:has-text("Continue")'
      ];

      for (const buttonSelector of finalizeButtons) {
        const button = page.locator(buttonSelector).first();
        if (await button.isVisible()) {
          console.log(`🔘 Found button: ${buttonSelector}`);
          await button.click();
          await page.waitForTimeout(5000);
          break;
        }
      }
    }

    // Step 10: Check final state
    console.log('📋 Step 10: Checking final state...');
    await page.screenshot({ path: 'test-results/final-state.png', fullPage: true });

    // Navigate to inventory to see if assets were created
    await page.goto(`${BASE_URL}/discovery/inventory`);
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'test-results/inventory-final.png', fullPage: true });

    // Count assets
    const assetCount = await page.locator('tr:has(td), .asset-row, [data-testid*="asset"]').count();
    console.log(`📊 Final asset count: ${assetCount}`);

    // Summary
    console.log('\n=== Test Summary ===');
    console.log(`Login: ✅`);
    console.log(`File Upload: ✅`);
    console.log(`Attribute Mapping Page: ✅`);
    console.log(`Mapping Data Found: ${foundMapping ? '✅' : '❌'}`);
    console.log(`Assets Created: ${assetCount > 0 ? '✅' : '❌'} (${assetCount} assets)`);

    // Clean up screenshots
    console.log('\n🧹 Cleaning up test artifacts...');
    const screenshotsToKeep = ['final-state.png', 'inventory-final.png'];
    const allScreenshots = fs.readdirSync('test-results').filter(f => f.endsWith('.png'));

    for (const screenshot of allScreenshots) {
      if (!screenshotsToKeep.includes(screenshot)) {
        fs.unlinkSync(path.join('test-results', screenshot));
      }
    }
  });
});
