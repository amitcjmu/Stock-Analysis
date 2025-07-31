import { test, expect, Page } from '@playwright/test';
import path from 'path';

test.describe('Discovery Flow Comprehensive E2E Test', () => {
  let flowId: string | null = null;
  const consoleErrors: string[] = [];
  const networkErrors: { url: string; status: number; error?: string }[] = [];

  test.beforeEach(async ({ page }) => {
    // Set up console error capturing
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Set up network error capturing
    page.on('response', (response) => {
      if (response.status() >= 400) {
        networkErrors.push({
          url: response.url(),
          status: response.status(),
          error: response.statusText()
        });
      }
    });

    // Navigate to login page
    await page.goto('http://localhost:8081/login');

    // Login with demo user credentials
    await page.fill('input[type="email"]', 'chocka@gmail.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for navigation to complete
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Report console errors
    if (consoleErrors.length > 0) {
      console.log('\n=== CONSOLE ERRORS ===');
      consoleErrors.forEach((error, index) => {
        console.log(`${index + 1}. ${error}`);
      });
    }

    // Report network errors
    if (networkErrors.length > 0) {
      console.log('\n=== NETWORK ERRORS ===');
      networkErrors.forEach((error, index) => {
        console.log(`${index + 1}. ${error.status} - ${error.url}`);
        if (error.error) console.log(`   Error: ${error.error}`);
      });
    }

    // Take screenshot on failure
    if (testInfo.status === 'failed') {
      await page.screenshot({
        path: `test-failure-${testInfo.title.replace(/\s+/g, '-')}-${Date.now()}.png`,
        fullPage: true
      });
    }
  });

  test('Complete Discovery Flow - From Import to Asset Inventory', async ({ page }) => {
    console.log('\n=== Starting Complete Discovery Flow Test ===\n');

    // Step 1: Navigate to Discovery
    console.log('Step 1: Navigating to Discovery...');
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);

    // Check if we're on overview page with flow sync issues
    const flowNotFound = await page.locator('text=/flow.*not.*found|Flow not found/i').isVisible();
    if (flowNotFound) {
      console.log('  - Flow not found detected, will navigate to CMDB Import');
    }

    // Step 2: Navigate to CMDB Import
    console.log('\nStep 2: Navigating to CMDB Import...');
    const cmdbImportButton = page.locator('button, a').filter({ hasText: /CMDB Import|Data Import/i }).first();

    if (await cmdbImportButton.isVisible()) {
      await cmdbImportButton.click();
    } else {
      // Try direct navigation through menu
      await page.click('text=Data Import');
    }

    await page.waitForURL('**/discovery/cmdb-import', { timeout: 10000 });
    console.log('  ✓ Successfully reached CMDB Import page');

    // Step 3: Upload CSV file
    console.log('\nStep 3: Uploading CSV file...');
    const testFilePath = path.join(__dirname, '../fixtures/test-cmdb-data.csv');

    // Find the upload area
    const uploadArea = page.locator('.border-dashed, .upload-area').first();
    const fileInput = page.locator('input[type="file"]');

    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles(testFilePath);
    } else {
      // Click upload area to trigger file input
      await uploadArea.click();
      await page.waitForSelector('input[type="file"]', { timeout: 5000 });
      await page.locator('input[type="file"]').setInputFiles(testFilePath);
    }

    console.log('  - File selected, waiting for upload to process...');

    // Wait for upload success
    await page.waitForTimeout(3000);

    // Check for flow ID
    const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
    const flowIdVisible = await flowIdElement.isVisible({ timeout: 10000 }).catch(() => false);

    if (flowIdVisible) {
      flowId = await flowIdElement.textContent();
      console.log(`  ✓ Flow ID created: ${flowId}`);
    } else {
      console.log('  ⚠ Flow ID not visible after upload');

      // Check for any error messages
      const errorMessage = await page.locator('text=/error|failed|unable/i').first().textContent().catch(() => null);
      if (errorMessage) {
        console.log(`  ✗ Error detected: ${errorMessage}`);
      }
    }

    // Check for success indicators
    const successIndicators = [
      'text=/Upload completed|Upload successful/i',
      'text=/Processing complete|Import successful/i',
      'text=/Data imported successfully/i'
    ];

    let uploadSuccess = false;
    for (const indicator of successIndicators) {
      if (await page.locator(indicator).isVisible({ timeout: 5000 }).catch(() => false)) {
        uploadSuccess = true;
        const successText = await page.locator(indicator).textContent();
        console.log(`  ✓ Upload success: ${successText}`);
        break;
      }
    }

    if (!uploadSuccess) {
      console.log('  ✗ No upload success indicator found');

      // Check API response
      const apiErrors = networkErrors.filter(e => e.url.includes('/api/v1/discovery'));
      if (apiErrors.length > 0) {
        console.log('  ✗ Discovery API errors detected:');
        apiErrors.forEach(e => console.log(`    - ${e.status}: ${e.url}`));
      }
    }

    // Step 4: Navigate to Attribute Mapping
    console.log('\nStep 4: Testing Attribute Mapping...');
    await page.click('text=Attribute Mapping');

    try {
      await page.waitForURL('**/discovery/attribute-mapping', { timeout: 10000 });
      console.log('  ✓ Successfully reached Attribute Mapping page');
    } catch (error) {
      console.log('  ✗ Failed to navigate to Attribute Mapping');
      return;
    }

    await page.waitForTimeout(3000);

    // Check for data on attribute mapping page
    const noDataMessage = await page.locator('text=/No Field Mapping Available|No data available/i').isVisible();

    if (noDataMessage) {
      console.log('  ✗ No field mapping data available');

      // Check if flow selector is present
      const flowSelector = page.locator('select[id*="flow"], .flow-selector').first();
      if (await flowSelector.isVisible()) {
        console.log('  - Flow selector found, attempting to select flow...');

        const options = await flowSelector.locator('option').all();
        console.log(`  - Found ${options.length} flow options`);

        if (options.length > 1) {
          await flowSelector.selectOption({ index: 1 });
          await page.waitForTimeout(2000);

          // Re-check for data
          const stillNoData = await page.locator('text=/No Field Mapping Available|No data available/i').isVisible();
          if (!stillNoData) {
            console.log('  ✓ Data loaded after flow selection');
          } else {
            console.log('  ✗ Still no data after flow selection');
          }
        }
      }

      // Check for specific error about missing child records
      const childTableError = await page.locator('text=/child.*table|field_mappings.*not found/i').isVisible();
      if (childTableError) {
        console.log('  ✗ CRITICAL: Child table records missing (field_mappings)');
      }
    } else {
      console.log('  ✓ Field mapping data is available');

      // Check for field mapping UI elements
      const fieldMappingElements = await page.locator('.field-mapping-item, [data-testid="field-mapping"]').count();
      console.log(`  - Found ${fieldMappingElements} field mapping elements`);

      // Check for preview data
      const previewData = await page.locator('text=/Preview|Sample Data/i').isVisible();
      if (previewData) {
        console.log('  ✓ Preview data section is visible');
      }
    }

    // Check for approve button
    const approveButton = page.locator('button').filter({ hasText: /Approve|Confirm|Next/i }).first();
    if (await approveButton.isVisible()) {
      console.log('  ✓ Approve button is available');
      await approveButton.click();
      await page.waitForTimeout(2000);
    }

    // Step 5: Check Data Cleansing Phase
    console.log('\nStep 5: Checking Data Cleansing phase...');

    // Try to navigate to Data Cleansing
    const dataCleansingLink = page.locator('a, button').filter({ hasText: /Data Cleansing|Cleansing/i }).first();
    if (await dataCleansingLink.isVisible()) {
      await dataCleansingLink.click();
      await page.waitForTimeout(2000);

      // Check for data quality metrics
      const qualityMetrics = await page.locator('text=/Quality|Accuracy|Completeness/i').isVisible();
      if (qualityMetrics) {
        console.log('  ✓ Data quality metrics are displayed');
      } else {
        console.log('  ✗ No data quality metrics found');
      }
    } else {
      console.log('  ⚠ Data Cleansing navigation not found');
    }

    // Step 6: Navigate to Asset Inventory
    console.log('\nStep 6: Checking Asset Inventory...');
    await page.click('text=Inventory');

    try {
      await page.waitForURL('**/discovery/inventory', { timeout: 10000 });
      console.log('  ✓ Successfully reached Inventory page');
    } catch (error) {
      console.log('  ✗ Failed to navigate to Inventory');
    }

    await page.waitForTimeout(3000);

    // Check for discovered assets
    const assetTable = await page.locator('table, .asset-list, [data-testid="asset-table"]').isVisible();
    if (assetTable) {
      const assetRows = await page.locator('tbody tr, .asset-item').count();
      console.log(`  ✓ Asset table visible with ${assetRows} assets`);

      if (assetRows === 0) {
        console.log('  ✗ No assets found in inventory');
      }
    } else {
      console.log('  ✗ No asset table/list found');

      // Check for "no data" message
      const noAssetsMessage = await page.locator('text=/No assets|No data|Empty/i').isVisible();
      if (noAssetsMessage) {
        console.log('  ✗ "No assets" message displayed');
      }
    }

    // Step 7: Check Dependencies
    console.log('\nStep 7: Checking Dependencies & Tech Debt...');

    // Navigate to Dependencies
    const dependenciesLink = page.locator('a, button').filter({ hasText: /Dependencies/i }).first();
    if (await dependenciesLink.isVisible()) {
      await dependenciesLink.click();
      await page.waitForTimeout(2000);

      const dependencyData = await page.locator('text=/Dependency|Dependencies found/i').isVisible();
      if (dependencyData) {
        console.log('  ✓ Dependency analysis data is visible');
      } else {
        console.log('  ✗ No dependency data found');
      }
    }

    // Check Tech Debt
    const techDebtLink = page.locator('a, button').filter({ hasText: /Tech Debt/i }).first();
    if (await techDebtLink.isVisible()) {
      await techDebtLink.click();
      await page.waitForTimeout(2000);

      const techDebtData = await page.locator('text=/Technical Debt|Risk Score/i').isVisible();
      if (techDebtData) {
        console.log('  ✓ Tech debt assessment is visible');
      } else {
        console.log('  ✗ No tech debt data found');
      }
    }

    // Final Summary
    console.log('\n=== TEST SUMMARY ===');
    console.log(`Flow ID: ${flowId || 'Not created'}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);

    // Check critical issues
    const criticalIssues = [];

    if (!flowId) {
      criticalIssues.push('Flow ID not created after upload');
    }

    if (networkErrors.some(e => e.url.includes('/api/v1/discovery') && e.status >= 500)) {
      criticalIssues.push('Server errors in Discovery API');
    }

    if (consoleErrors.some(e => e.includes('Discovery flow not found'))) {
      criticalIssues.push('Discovery flow not found errors');
    }

    if (consoleErrors.some(e => e.includes('field_mappings'))) {
      criticalIssues.push('Field mappings table issues');
    }

    if (criticalIssues.length > 0) {
      console.log('\n=== CRITICAL ISSUES FOUND ===');
      criticalIssues.forEach((issue, index) => {
        console.log(`${index + 1}. ${issue}`);
      });
    }

    // Recommendations
    console.log('\n=== RECOMMENDATIONS ===');
    if (!flowId) {
      console.log('1. Check that flow creation API properly returns flow_id');
      console.log('2. Verify both master and child flow records are created');
    }

    if (networkErrors.length > 0) {
      console.log('3. Fix API endpoints returning errors');
    }

    if (consoleErrors.length > 0) {
      console.log('4. Address JavaScript console errors');
    }
  });

  test('Test Flow State Persistence', async ({ page }) => {
    console.log('\n=== Testing Flow State Persistence ===\n');

    // First create a flow
    await page.click('text=Discovery');
    await page.waitForTimeout(2000);

    // Navigate to CMDB Import
    await page.click('text=/CMDB Import|Data Import/i');
    await page.waitForURL('**/discovery/cmdb-import', { timeout: 10000 });

    // Upload file
    const testFilePath = path.join(__dirname, '../fixtures/test-cmdb-data.csv');
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);

    await page.waitForTimeout(3000);

    // Capture flow ID
    const flowIdElement = page.locator('text=/flow-\\d{8}-\\d{6}/');
    const flowIdText = await flowIdElement.textContent().catch(() => null);

    if (flowIdText) {
      console.log(`Flow created: ${flowIdText}`);

      // Navigate away and come back
      await page.click('text=Dashboard');
      await page.waitForTimeout(2000);

      await page.click('text=Discovery');
      await page.waitForTimeout(2000);

      // Check if flow is still recognized
      const flowStillExists = await page.locator(`text=${flowIdText}`).isVisible({ timeout: 5000 }).catch(() => false);

      if (flowStillExists) {
        console.log('  ✓ Flow persisted across navigation');
      } else {
        console.log('  ✗ Flow lost after navigation');

        // Check for "flow not found" error
        const flowNotFound = await page.locator('text=/flow.*not.*found/i').isVisible();
        if (flowNotFound) {
          console.log('  ✗ CRITICAL: Flow state not persisting properly');
        }
      }
    }
  });

  test('Test Error Handling and Recovery', async ({ page }) => {
    console.log('\n=== Testing Error Handling ===\n');

    // Test upload with invalid file
    await page.click('text=Discovery');
    await page.click('text=/CMDB Import|Data Import/i');
    await page.waitForURL('**/discovery/cmdb-import', { timeout: 10000 });

    // Create an invalid file
    const invalidFilePath = path.join(__dirname, '../fixtures/invalid-file.txt');

    // Try to upload invalid file
    const fileInput = page.locator('input[type="file"]');

    try {
      await fileInput.setInputFiles(invalidFilePath);
      await page.waitForTimeout(2000);

      // Check for error handling
      const errorMessage = await page.locator('text=/error|invalid|failed/i').first().isVisible({ timeout: 5000 });

      if (errorMessage) {
        console.log('  ✓ Error message displayed for invalid file');
        const errorText = await page.locator('text=/error|invalid|failed/i').first().textContent();
        console.log(`  - Error: ${errorText}`);
      } else {
        console.log('  ✗ No error message for invalid file');
      }
    } catch (error) {
      console.log('  ⚠ Could not test invalid file upload');
    }
  });
});
