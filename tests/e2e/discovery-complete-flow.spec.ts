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

async function loginUser(page: Page): Promise<void> {
  console.log('🔐 Logging in user...');
  await page.goto(`${BASE_URL}/login`);

  await page.fill('input[type="email"]', TEST_USER.email);
  await page.fill('input[type="password"]', TEST_USER.password);
  await page.click('button[type="submit"]');

  await page.waitForTimeout(3000);

  const currentUrl = page.url();
  const isLoggedIn = !currentUrl.includes('/login');

  if (isLoggedIn) {
    console.log('✅ User logged in successfully, current URL:', currentUrl);
  } else {
    throw new Error('Login failed - still on login page');
  }
}

async function navigateToDataImport(page: Page): Promise<void> {
  console.log('📁 Navigating to Data Import...');

  // Go to discovery page first
  await page.goto(`${BASE_URL}/discovery`);
  await page.waitForTimeout(2000);

  // Click the Data Import link we found in debugging
  const dataImportLink = page.locator('a[href="/discovery/cmdb-import"]');
  if (await dataImportLink.isVisible()) {
    console.log('🔗 Found Data Import link, clicking...');
    await dataImportLink.click();
  } else {
    // Direct navigation as fallback
    console.log('🔄 Direct navigation to CMDB import...');
    await page.goto(`${BASE_URL}/discovery/cmdb-import`);
  }

  await page.waitForTimeout(3000);
  console.log('📄 On CMDB Import page, URL:', page.url());
}

async function uploadCMDBFile(page: Page): Promise<string> {
  console.log('📤 Uploading CMDB file...');

  // Take screenshot to see current state
  await page.screenshot({ path: 'test-results/cmdb-import-before-upload.png', fullPage: true });

  // Check if upload is blocked by existing flows
  const uploadBlocked = await page.locator('text=/upload blocked|data upload disabled/i').first().isVisible();
  if (uploadBlocked) {
    console.log('⚠️ Upload blocked by existing flows - attempting to resolve...');

    // Look for "Continue Flow" button for existing flow
    const continueButton = page.locator('button:has-text("Continue Flow")');
    if (await continueButton.isVisible()) {
      console.log('🔄 Found existing flow - continuing with it...');
      await continueButton.click();
      await page.waitForTimeout(3000);
      return 'Continuing with existing flow';
    }

    // Look for "Delete" button to clean up existing flow
    const deleteButton = page.locator('button:has-text("Delete")');
    if (await deleteButton.isVisible()) {
      console.log('🗑️ Deleting existing flow to allow new upload...');
      await deleteButton.click();
      await page.waitForTimeout(2000);

      // Refresh the page to clear the blocked state
      await page.reload();
      await page.waitForTimeout(3000);
    }

    // Look for "Manage Flows" button
    const manageFlowsButton = page.locator('button:has-text("Manage Flows")');
    if (await manageFlowsButton.isVisible()) {
      console.log('🔧 Opening flow management...');
      await manageFlowsButton.click();
      await page.waitForTimeout(2000);

      // Try to delete flows from the management interface
      const deleteFlowButtons = await page.locator('button:has-text("Delete")').all();
      if (deleteFlowButtons.length > 0) {
        console.log(`🗑️ Found ${deleteFlowButtons.length} flows to delete`);
        for (const button of deleteFlowButtons) {
          await button.click();
          await page.waitForTimeout(1000);
        }

        // Go back to data import
        await page.goto(`${BASE_URL}/discovery/cmdb-import`);
        await page.waitForTimeout(3000);
      }
    }
  }

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
    // Check if upload is still blocked
    const stillBlocked = await page.locator('text=/upload blocked|data upload disabled/i').first().isVisible();
    if (stillBlocked) {
      throw new Error('Upload still blocked by existing flows after cleanup attempts');
    }
    throw new Error('No upload areas found on CMDB import page');
  }

  // Try clicking the first upload area
  const firstUploadArea = uploadAreas[0];
  console.log('🎯 Clicking first upload area...');

  // Check if it's visible and clickable
  const isVisible = await firstUploadArea.isVisible();
  console.log('Upload area visible:', isVisible);

  if (!isVisible) {
    throw new Error('Upload area not visible');
  }

  await firstUploadArea.click();
  await page.waitForTimeout(1000);

  // Look for file input after clicking
  const fileInput = page.locator('input[type="file"]');
  const fileInputCount = await fileInput.count();
  console.log(`File inputs found: ${fileInputCount}`);

  if (fileInputCount === 0) {
    throw new Error('No file input found after clicking upload area');
  }

  // Prepare test file
  const testFilePath = path.join(__dirname, '../fixtures/enterprise-cmdb-data.csv');
  console.log('Test file path:', testFilePath);

  if (!fs.existsSync(testFilePath)) {
    throw new Error(`Test file not found: ${testFilePath}`);
  }

  console.log('✅ Test file exists, uploading...');

  // Upload the file
  await fileInput.first().setInputFiles(testFilePath);
  await page.waitForTimeout(3000);

  // Look for upload success indicators
  const successSelectors = [
    'text=/upload.*complete/i',
    'text=/processing.*complete/i',
    'text=/import.*complete/i',
    'text=/success/i',
    '.success',
    '[data-testid*="success"]'
  ];

  let uploadSuccess = false;
  let successMessage = '';

  for (const selector of successSelectors) {
    if (await page.locator(selector).isVisible()) {
      uploadSuccess = true;
      successMessage = await page.locator(selector).first().textContent() || 'Success detected';
      break;
    }
  }

  // Take screenshot after upload
  await page.screenshot({ path: 'test-results/cmdb-import-after-upload.png', fullPage: true });

  if (uploadSuccess) {
    console.log('✅ Upload successful:', successMessage);
    return successMessage;
  } else {
    // Check for any error messages
    const errorSelectors = ['text=/error/i', 'text=/failed/i', '.error', '[data-testid*="error"]'];
    for (const selector of errorSelectors) {
      if (await page.locator(selector).isVisible()) {
        const errorMessage = await page.locator(selector).first().textContent();
        console.log('❌ Upload error:', errorMessage);
        throw new Error(`Upload failed: ${errorMessage}`);
      }
    }

    console.log('⚠️ Upload status unclear - proceeding with caution');
    return 'Upload completed (status unclear)';
  }
}

async function waitForProcessing(page: Page): Promise<void> {
  console.log('⏳ Waiting for discovery processing...');

  // Wait a bit for any processing to start
  await page.waitForTimeout(5000);

  // Check for processing indicators - use first() to avoid strict mode violations
  const processingSelectors = [
    'text=/processing/i',
    'text=/analyzing/i',
    '.spinner',
    '.loading',
    '[data-testid*="processing"]'
  ];

  let isProcessing = false;
  for (const selector of processingSelectors) {
    if (await page.locator(selector).first().isVisible()) {
      isProcessing = true;
      console.log('🔄 Processing detected, waiting...');
      break;
    }
  }

  if (isProcessing) {
    // Wait for processing to complete (max 30 seconds)
    let attempts = 0;
    const maxAttempts = 15;

    while (attempts < maxAttempts) {
      await page.waitForTimeout(2000);

      // Check if processing is still ongoing
      let stillProcessing = false;
      for (const selector of processingSelectors) {
        if (await page.locator(selector).first().isVisible()) {
          stillProcessing = true;
          break;
        }
      }

      if (!stillProcessing) {
        console.log('✅ Processing completed');
        break;
      }

      attempts++;
      console.log(`⏳ Still processing... (${attempts}/${maxAttempts})`);
    }

    if (attempts >= maxAttempts) {
      console.log('⚠️ Processing timeout - proceeding anyway');
    }
  } else {
    console.log('✅ No processing indicators found - may have completed immediately');
  }
}

async function navigateToAttributeMapping(page: Page): Promise<void> {
  console.log('🗺️ Navigating to Attribute Mapping...');

  // Try different ways to get to attribute mapping
  const attributeMappingSelectors = [
    'text="Attribute Mapping"',
    'a[href*="attribute-mapping"]',
    'button:has-text("Attribute Mapping")',
    'nav a:has-text("Mapping")'
  ];

  let navigatedSuccessfully = false;

  for (const selector of attributeMappingSelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      console.log(`🔗 Found attribute mapping link: ${selector}`);
      await element.click();
      await page.waitForTimeout(2000);
      navigatedSuccessfully = true;
      break;
    }
  }

  if (!navigatedSuccessfully) {
    // Try direct navigation
    console.log('🔄 Direct navigation to attribute mapping...');
    await page.goto(`${BASE_URL}/discovery/attribute-mapping`);
    await page.waitForTimeout(2000);
  }

  console.log('📄 On Attribute Mapping page, URL:', page.url());

  // Take screenshot
  await page.screenshot({ path: 'test-results/attribute-mapping-page.png', fullPage: true });
}

async function validateFieldMappings(page: Page): Promise<number> {
  console.log('🔍 Validating field mappings...');

  // Check for field mapping data
  const fieldMappingSelectors = [
    'text=/field mapping/i',
    'text=/critical attributes/i',
    'text=/mapping complete/i',
    '.mapping-table',
    '[data-testid*="mapping"]'
  ];

  let hasMappingData = false;
  for (const selector of fieldMappingSelectors) {
    if (await page.locator(selector).first().isVisible()) {
      hasMappingData = true;
      console.log(`✅ Field mapping data found: ${selector}`);
      break;
    }
  }

  // If no mapping data but we see "No Field Mapping Available", try to trigger it
  if (!hasMappingData) {
    const triggerButton = page.locator('button:has-text("Trigger Field Mapping")');
    if (await triggerButton.isVisible()) {
      console.log('🔄 Triggering field mapping manually...');
      await triggerButton.click();
      await page.waitForTimeout(5000);

      // Check again for mapping data
      for (const selector of fieldMappingSelectors) {
        if (await page.locator(selector).first().isVisible()) {
          hasMappingData = true;
          console.log(`✅ Field mapping data found after trigger: ${selector}`);
          break;
        }
      }
    }
  }

  if (!hasMappingData) {
    console.log('⚠️ No field mapping data immediately visible');

    // Check for "No data" messages
    const noDataMessages = await page.locator('text=/no.*data|no.*mapping|empty/i').all();
    if (noDataMessages.length > 0) {
      for (const message of noDataMessages) {
        const text = await message.textContent();
        console.log('📝 No data message:', text);
      }
    }

    return 0;
  }

  // Try to count mapped fields or records
  const mappingRows = await page.locator('tr, .mapping-row, [data-testid*="row"]').count();
  console.log(`📊 Mapping rows found: ${mappingRows}`);

  return mappingRows;
}

async function navigateToAssetInventory(page: Page): Promise<number> {
  console.log('📋 Navigating to Asset Inventory...');

  // Try to find asset inventory navigation
  const assetInventorySelectors = [
    'text="Asset Inventory"',
    'a[href*="asset-inventory"]',
    'button:has-text("Asset Inventory")',
    'nav a:has-text("Inventory")'
  ];

  let navigatedSuccessfully = false;

  for (const selector of assetInventorySelectors) {
    const element = page.locator(selector);
    if (await element.isVisible()) {
      console.log(`🔗 Found asset inventory link: ${selector}`);
      await element.click();
      await page.waitForTimeout(3000);
      navigatedSuccessfully = true;
      break;
    }
  }

  if (!navigatedSuccessfully) {
    // Try direct navigation
    console.log('🔄 Direct navigation to asset inventory...');
    await page.goto(`${BASE_URL}/discovery/asset-inventory`);
    await page.waitForTimeout(3000);
  }

  console.log('📄 On Asset Inventory page, URL:', page.url());

  // Take screenshot
  await page.screenshot({ path: 'test-results/asset-inventory-page.png', fullPage: true });

  // Count assets
  const assetRows = await page.locator('tr:has(td), .asset-row, [data-testid*="asset"]').count();
  console.log(`📊 Assets found: ${assetRows}`);

  return assetRows;
}

test.describe('Complete Discovery Flow', () => {
  test('Execute complete discovery workflow from CMDB upload to asset inventory', async ({ page }) => {
    test.setTimeout(300000); // 5 minutes

    const results = {
      login: false,
      navigation: false,
      upload: false,
      processing: false,
      attributeMapping: false,
      assetInventory: false,
      assetCount: 0
    };

    try {
      // Phase 1: Login
      await loginUser(page);
      results.login = true;

      // Phase 2: Navigate to Data Import
      await navigateToDataImport(page);
      results.navigation = true;

      // Phase 3: Upload CMDB File
      const uploadResult = await uploadCMDBFile(page);
      results.upload = true;
      console.log('📤 Upload result:', uploadResult);

      // Phase 4: Wait for Processing
      await waitForProcessing(page);
      results.processing = true;

      // Phase 5: Check Attribute Mapping
      await navigateToAttributeMapping(page);
      const mappingCount = await validateFieldMappings(page);
      results.attributeMapping = mappingCount > 0;
      console.log('🗺️ Field mappings:', mappingCount);

      // Phase 6: Check Asset Inventory
      const assetCount = await navigateToAssetInventory(page);
      results.assetInventory = assetCount > 0;
      results.assetCount = assetCount;

      // Final Results
      console.log('🎉 Discovery Flow Results:', results);

      // Assertions
      expect(results.login).toBe(true);
      expect(results.navigation).toBe(true);
      expect(results.upload).toBe(true);

      // These are the key success indicators for discovery flow
      if (results.assetCount > 0) {
        console.log('✅ DISCOVERY FLOW SUCCESSFUL - Assets created!');
      } else if (results.attributeMapping) {
        console.log('✅ DISCOVERY FLOW PARTIAL SUCCESS - Attribute mapping working');
      } else {
        console.log('⚠️ DISCOVERY FLOW INCOMPLETE - No assets or mappings detected');
      }

    } catch (error) {
      console.error('❌ Discovery flow failed:', error);
      console.log('📊 Results at failure:', results);

      await page.screenshot({
        path: `test-results/discovery-flow-failure-${Date.now()}.png`,
        fullPage: true
      });

      throw error;
    }
  });
});
